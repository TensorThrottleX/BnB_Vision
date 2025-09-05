from .base import DataSource, SourceResult, register_source
from src.downloader import download_dataset
from src.data_preprocessing import load_data, clean_data
from src.scraper import DatasetVersion

@register_source
class InsideAirbnbSource(DataSource):
    source_type = "InsideAirbnb"
    def load(self) -> SourceResult:
        version: DatasetVersion = self.params["version"]
        city: str = self.params["city"]
        date: str = self.params["date"]
        force: bool = self.params.get("force", False)
        override_url = self.params.get("override_listings_url")
        allow_cached = self.params.get("allow_cached_if_blocked", True)
        files = download_dataset(
            version,
            city=city,
            date=date,
            force=force,
            override_listings_url=override_url,
            allow_cached_if_blocked=allow_cached
        )
        df = load_data(files["listings"], files["reviews"], files["neighbourhoods"])
        df = clean_data(df, save_path=f"data/processed/{city}_{date}_clean.csv")
        meta = {
            "source_label": f"{city} {date}",
            "files": files,
            "blocked": files.get("blocked"),
            "status_info": files.get("status_info")
        }
        return SourceResult(df=df, metadata=meta)