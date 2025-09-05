from .base import DataSource, SourceResult, register_source
from src.data_preprocessing import clean_data
import pandas as pd

@register_source
class CSVUploadSource(DataSource):
    source_type = "LocalCSVUpload"
    def load(self) -> SourceResult:
        listings_file = self.params["listings_file"]
        reviews_file = self.params.get("reviews_file")
        df = pd.read_csv(listings_file)
        if reviews_file:
            rev_df = pd.read_csv(reviews_file)
            if "id" in df.columns and "listing_id" in rev_df.columns:
                counts = rev_df.groupby("listing_id").size().rename("num_reviews")
                df = df.merge(counts, left_on="id", right_index=True, how="left")
        df = clean_data(df, save_path="data/processed/manual_clean.csv")
        return SourceResult(df=df, metadata={"source_label": "Manual Upload"})