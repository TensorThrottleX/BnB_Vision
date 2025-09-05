import pandas as pd

def get_column(df, names):
    """
    Find a column that matches any name in the list, with some fuzziness.
    """
    for name in names:
        if name in df.columns:
            return name
    for col in df.columns:
        for name in names:
            if name.lower() in col.lower():
                return col
    return None

def safe_mean(series):
    """
    Return the mean of a series, converting to numbers if needed.
    """
    try:
        return pd.to_numeric(series, errors='coerce').mean()
    except Exception:
        return None

def amenities_count(series):
    """
    Count amenities if given as a stringified list, e.g. "[wifi, kitchen, ...]".
    """
    def count(x):
        if pd.isnull(x):
            return 0
        if isinstance(x, str) and x.strip().startswith("["):
            try:
                return len(eval(x))
            except Exception:
                return 0
        return 0
    return series.apply(count)

def compute_metrics(df):
    """
    Calculate averages and totals for key listing attributes.
    Returns a dictionary and the price column used.
    """
    metrics = {}
    price_col = get_column(df, ['price', 'nightly_price', 'total_price', 'cost'])
    amenities_col = get_column(df, ['amenities_count', 'amenities'])
    reviews_col = get_column(df, ['number_of_reviews', 'num_reviews', 'reviews_count'])
    rating_col = get_column(df, ['review_scores_rating', 'rating'])
    avail_col = get_column(df, ['availability_365', 'availability'])

    metrics['avg_price'] = safe_mean(df[price_col]) if price_col else None
    metrics['avg_reviews'] = safe_mean(df[reviews_col]) if reviews_col else None
    metrics['avg_rating'] = safe_mean(df[rating_col]) if rating_col else None
    metrics['avg_availability'] = safe_mean(df[avail_col]) if avail_col else None

    if amenities_col:
        if pd.api.types.is_numeric_dtype(df[amenities_col]):
            metrics['avg_amenities'] = safe_mean(df[amenities_col])
        else:
            metrics['avg_amenities'] = amenities_count(df[amenities_col]).mean()
    else:
        metrics['avg_amenities'] = None

    metrics['listings'] = len(df)
    return metrics, price_col