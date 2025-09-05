import pandas as pd

REQUIRED = ["id", "price", "latitude", "longitude"]

def assert_basic_schema(df: pd.DataFrame):
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # unify review counts
    if "num_reviews" in df.columns and "number_of_reviews" not in df.columns:
        df.rename(columns={"num_reviews": "number_of_reviews"}, inplace=True)
    return df