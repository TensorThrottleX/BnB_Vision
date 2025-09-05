from __future__ import annotations
from .base import BaseExtractor, ExtractionResult
from typing import List, Dict, Any
import json

STRUCTURED_TYPES = {
    "Offer", "Product", "Hotel", "LodgingBusiness",
    "Accommodation", "Apartment", "House", "Room", "LocalBusiness"
}

class StructuredDataExtractor(BaseExtractor):
    name = "structured_data"

    def can_handle(self, url: str, html_text: str | None = None) -> bool:
        return True  # Always attempt

    def extract(self, url: str, html_text: str) -> ExtractionResult:
        records: List[Dict[str, Any]] = []
        meta = {"method": None, "extractor": self.name}

        try:
            import extruct
            from w3lib.html import get_base_url
            base_url = get_base_url(html_text, url)
            data = extruct.extract(html_text, base_url=base_url, syntaxes=["json-ld", "microdata"])
            meta["method"] = "extruct"
            flatten: List[Dict[str, Any]] = []
            for key, arr in data.items():
                if isinstance(arr, list):
                    for obj in arr:
                        if isinstance(obj, dict):
                            if "@graph" in obj and isinstance(obj["@graph"], list):
                                for g in obj["@graph"]:
                                    if isinstance(g, dict):
                                        flatten.append(g)
                            else:
                                flatten.append(obj)
            for node in flatten:
                t = node.get("@type")
                types = set()
                if isinstance(t, str): types.add(t)
                elif isinstance(t, list): types |= set(map(str, t))
                if not types & STRUCTURED_TYPES:
                    continue
                name = node.get("name") or node.get("title")
                url_field = node.get("url") or url
                offers = node.get("offers")
                price = None
                if isinstance(offers, dict):
                    price = offers.get("price")
                elif isinstance(offers, list) and offers:
                    if isinstance(offers[0], dict):
                        price = offers[0].get("price")
                agg = node.get("aggregateRating")
                rating = None
                review_count = None
                if isinstance(agg, dict):
                    rating = agg.get("ratingValue")
                    review_count = agg.get("reviewCount")
                records.append({
                    "source": "structured",
                    "title": name,
                    "url": url_field,
                    "price": price,
                    "raw_price": price,
                    "rating": rating,
                    "review_count": review_count
                })
        except ImportError:
            # Fallback simple JSON-LD scan
            from bs4 import BeautifulSoup
            meta["method"] = "jsonld_fallback"
            soup = BeautifulSoup(html_text, "lxml")
            scripts = soup.find_all("script", {"type": "application/ld+json"})
            for sc in scripts:
                try:
                    data = json.loads(sc.string or "")
                except Exception:
                    continue
                nodes = data
                if isinstance(data, dict) and "@graph" in data and isinstance(data["@graph"], list):
                    nodes = data["@graph"]
                if not isinstance(nodes, list):
                    nodes = [nodes]
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    t = node.get("@type")
                    types = set()
                    if isinstance(t, str): types.add(t)
                    elif isinstance(t, list): types |= set(t)
                    if not types & STRUCTURED_TYPES:
                        continue
                    name = node.get("name") or node.get("title")
                    url_field = node.get("url") or url
                    price = None
                    offers = node.get("offers")
                    if isinstance(offers, dict):
                        price = offers.get("price")
                    rating = None
                    review_count = None
                    agg = node.get("aggregateRating")
                    if isinstance(agg, dict):
                        rating = agg.get("ratingValue")
                        review_count = agg.get("reviewCount")
                    records.append({
                        "source": "structured",
                        "title": name,
                        "url": url_field,
                        "price": price,
                        "raw_price": price,
                        "rating": rating,
                        "review_count": review_count
                    })

        return ExtractionResult(records=records, meta=meta)