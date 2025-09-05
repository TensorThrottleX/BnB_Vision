from __future__ import annotations
import pandas as pd
from src.utils.safe_io import safe_read_listings, FileFormatError

def load_data(
    listings_p: str,
    reviews_p: str | None = None,
    neighborhoods_p: str | None = None
) -> pd.DataFrame:
    """
    Loads and merges listings CSV (required), plus reviews and neighborhood CSVs (optional).
    Returns a DataFrame with merged columns if possible.
    """
    try:
        listings_df = safe_read_listings(listings_p)
    except FileFormatError as e:
        raise RuntimeError(f"Listings file invalid: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error reading listings: {e}")

    # Merge reviews if provided
    if reviews_p:
        try:
            reviews_df = pd.read_csv(reviews_p)
            # If reviews have 'listing_id', merge number of reviews to listings
            if "id" in listings_df.columns and "listing_id" in reviews_df.columns:
                count_series = reviews_df.groupby("listing_id").size().rename("num_reviews")
                listings_df = listings_df.merge(count_series, left_on="id", right_index=True, how="left")
        except Exception:
            pass  # Reviews are optional

    # Merge neighborhoods if desired (skipped in most cases)
    # You can add neighborhood merging logic if needed

    return listings_df

def clean_data(df: pd.DataFrame, save_path: str | None = None) -> pd.DataFrame:
    """
    Cleans up columns and types in the given DataFrame.
    - Converts price, latitude, longitude to numeric.
    - Saves to CSV if save_path is provided.
    """
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Add more cleaning steps as needed

    if save_path is not None:
        df.to_csv(save_path, index=False)
    return df