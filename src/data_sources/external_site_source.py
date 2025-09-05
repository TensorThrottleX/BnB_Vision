from .base import DataSource, SourceResult, register_source
from src.data_preprocessing import clean_data
import pandas as pd
import requests
from bs4 import BeautifulSoup

@register_source
class ExternalSiteSource(DataSource):
    source_type = "ExternalSiteURL"
    def _extract_field(self, node, cfg):
        sel = cfg.get("selector")
        attr = cfg.get("attr", "text")
        target = node.select_one(sel) if sel else node
        if not target:
            return None
        if attr == "text":
            return target.get_text(strip=True)
        if attr.startswith("data-"):
            return target.get(attr)
        return target.get(attr)
    def load(self) -> SourceResult:
        url: str = self.params["url"]
        listing_selector: str = self.params.get("listing_selector")
        field_map = self.params.get("field_map", {})
        resp = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        listing_nodes = soup.select(listing_selector) if listing_selector else []
        rows = []
        for ln in listing_nodes:
            row = {}
            for col, cfg in field_map.items():
                row[col] = self._extract_field(ln, cfg)
            rows.append(row)
        df = pd.DataFrame(rows)
        if "price_raw" in df.columns:
            df["price"] = (
                df["price_raw"].astype(str)
                .str.replace(r"[^\d\.]", "", regex=True)
                .replace("", "0").astype(float)
            )
        if "lat_raw" in df.columns:
            df["latitude"] = pd.to_numeric(df["lat_raw"], errors="coerce")
        if "lon_raw" in df.columns:
            df["longitude"] = pd.to_numeric(df["lon_raw"], errors="coerce")
        if "amenities_raw" in df.columns:
            df["amenities_list"] = (
                df["amenities_raw"].astype(str)
                .str.split("[,|]", regex=True)
                .apply(lambda x: [a.strip().lower() for a in x if a.strip()] if isinstance(x, list) else [])
            )
            df["amenities_count"] = df["amenities_list"].apply(len)
        if "id" not in df.columns:
            df["id"] = df.index.astype(str)
        df = clean_data(df, save_path="data/processed/external_clean.csv")
        meta = {
            "source_label": "External Site",
            "url": url,
            "extracted_rows": len(df)
        }
        return SourceResult(df=df, metadata=meta)