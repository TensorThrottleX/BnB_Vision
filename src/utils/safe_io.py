import pandas as pd

class FileFormatError(Exception):
    pass

def safe_read_listings(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise FileFormatError(f"Could not read file: {e}")
    # Add custom validation here if needed
    return df