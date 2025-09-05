from .base import DataSource, SourceResult, register_source
from src.data_preprocessing import clean_data
import pandas as pd
import requests
import gzip
from io import BytesIO, StringIO

@register_source
class DirectCSVURLSource(DataSource):
    source_type = "DirectCSVURL"
    def load(self) -> SourceResult:
        url: str = self.params["url"]
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        content = r.content
        if url.endswith(".gz"):
            with gzip.GzipFile(fileobj=BytesIO(content)) as gz:
                text = gz.read().decode("utf-8", errors="replace")
            df = pd.read_csv(StringIO(text))
        else:
            df = pd.read_csv(BytesIO(content))
        df = clean_data(df, save_path="data/processed/direct_url_clean.csv")
        meta = {"source_label": "Direct CSV URL", "url": url}
        return SourceResult(df=df, metadata=meta)