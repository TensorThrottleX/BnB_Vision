from __future__ import annotations
import math
import numpy as np
import pandas as pd
from typing import List, Optional

def _norm(series):
    if series is None or len(series) == 0:
        return np.zeros(len(series))
    s = series.astype(float)
    mn, mx = s.min(), s.max()
    if mx == mn:
        return np.zeros(len(s))
    return (s - mn) / (mx - mn)

def build_recommendation_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "predicted_price" in df.columns and "price" in df.columns:
        raw_val = (df["predicted_price"] - df["price"]) / df["predicted_price"].clip(lower=1)
        price_value = raw_val.clip(-1, 1)
    else:
        price_value = np.zeros(len(df))

    reviews_col = next((c for c in ["number_of_reviews","num_reviews","reviews_count"] if c in df.columns), None)
    if reviews_col:
        rev_component = np.log1p(df[reviews_col].fillna(0))
    else:
        rev_component = np.zeros(len(df))

    if "review_scores_rating" in df.columns:
        rating_factor = df["review_scores_rating"].fillna(0) / 100.0
    else:
        rating_factor = 1.0

    review_quality = _norm(rev_component * rating_factor)

    if "amenities_count" in df.columns:
        amenity_richness = _norm(df["amenities_count"].fillna(0))
    else:
        amenity_richness = np.zeros(len(df))

    if "availability_365" in df.columns:
        avail = df["availability_365"].fillna(0).clip(0,365)
        availability_score = 1 - ((avail - 180) ** 2) / (180 ** 2)
        availability_score = availability_score.clip(lower=0)
    else:
        availability_score = np.zeros(len(df))
    availability_score = _norm(pd.Series(availability_score))

    total_score = (
        0.40 * price_value +
        0.25 * review_quality +
        0.20 * amenity_richness +
        0.15 * availability_score
    )

    df["score_price_value"] = price_value
    df["score_review_quality"] = review_quality
    df["score_amenities"] = amenity_richness
    df["score_availability"] = availability_score
    df["total_score"] = total_score

    reasons = []
    for _, row in df.iterrows():
        r_parts = []
        if "predicted_price" in row and "price" in row and not math.isnan(row["price"]):
            diff = row["predicted_price"] - row["price"]
            pct = diff / row["price"] * 100 if row["price"] else 0
            if pct > 8:
                r_parts.append(f"~{pct:.0f}% undervalued")
            elif pct < -8:
                r_parts.append(f"{abs(pct):.0f}% premium")

        rev_c = reviews_col
        if rev_c and row.get(rev_c, 0) > 50:
            r_parts.append(f"{int(row[rev_c])} reviews")
        elif rev_c and row.get(rev_c, 0) > 10:
            r_parts.append("solid reviews")

        if "review_scores_rating" in row and not math.isnan(row["review_scores_rating"]):
            if row["review_scores_rating"] >= 95:
                r_parts.append("excellent rating")
            elif row["review_scores_rating"] >= 90:
                r_parts.append("strong rating")

        if "amenities_count" in row:
            if row["amenities_count"] >= 20:
                r_parts.append("rich amenities")
            elif row["amenities_count"] >= 10:
                r_parts.append("good amenities")

        if "availability_365" in row:
            av = row["availability_365"]
            if 60 <= av <= 250:
                r_parts.append("balanced availability")
            elif av < 30:
                r_parts.append("limited availability")

        if not r_parts:
            r_parts = ["meets criteria"]
        reasons.append("; ".join(r_parts))
    df["recommendation_reason"] = reasons
    return df

def filter_by_preferences(
    df: pd.DataFrame,
    price_range: Optional[tuple[float,float]] = None,
    reviews_range: Optional[tuple[int,int]] = None,
    stars_range: Optional[tuple[float,float]] = None,
    availability_range: Optional[tuple[int,int]] = None,
    occupancy_group: Optional[str] = None,
    room_types: Optional[List[str]] = None,
    required_amenities: Optional[List[str]] = None,
    min_amenities_count: Optional[int] = None,
    min_value_score: Optional[float] = None,
    max_price_per_person: Optional[float] = None
) -> pd.DataFrame:
    out = df.copy()

    # Price range
    if price_range and "price" in out.columns:
        lo, hi = price_range
        out = out[(out["price"] >= lo) & (out["price"] <= hi)]

    # Reviews
    if reviews_range:
        lo_r, hi_r = reviews_range
        rev_col = next((c for c in ["number_of_reviews","num_reviews","reviews_count"] if c in out.columns), None)
        if rev_col:
            out = out[out[rev_col].fillna(0).between(lo_r, hi_r)]

    # Stars (convert 1–5 to rating 0–100)
    if stars_range and "review_scores_rating" in out.columns:
        lo_s, hi_s = stars_range
        lo_real = (lo_s - 0.0) * 20  # inclusive
        hi_real = hi_s * 20
        out = out[out["review_scores_rating"].fillna(0).between(lo_real, hi_real)]

    # Availability
    if availability_range and "availability_365" in out.columns:
        alo, ahi = availability_range
        out = out[out["availability_365"].fillna(0).between(alo, ahi)]

    # Occupancy group
    if occupancy_group and "accommodates" in out.columns:
        mapping = {
            "Solo (1)": (1,1),
            "Duo (2)": (2,2),
            "Small group (3-4)": (3,4),
            "Family (5-6)": (5,6),
            "Large (7+)": (7, 99)
        }
        if occupancy_group in mapping:
            lo_a, hi_a = mapping[occupancy_group]
            out = out[out["accommodates"].fillna(0).between(lo_a, hi_a)]

    # Room types multi-select
    if room_types and "room_type" in out.columns and len(room_types):
        out = out[out["room_type"].isin(room_types)]

    # Amenities list
    if required_amenities and "amenities_list" in out.columns:
        req = [r.lower() for r in required_amenities]
        mask = []
        for lst in out["amenities_list"]:
            st_lower = {x.lower() for x in lst}
            mask.append(all(r in st_lower for r in req))
        out = out[pd.Series(mask, index=out.index)]

    # Minimum amenities count
    if min_amenities_count is not None and "amenities_count" in out.columns:
        out = out[out["amenities_count"].fillna(0) >= min_amenities_count]

    # Minimum value score (score_price_value)
    if min_value_score is not None and "score_price_value" in out.columns:
        out = out[out["score_price_value"] >= min_value_score]

    # Max price per person
    if max_price_per_person is not None and "accommodates" in out.columns and "price" in out.columns:
        ppp = out["price"] / out["accommodates"].replace(0, 1)
        out = out[ppp <= max_price_per_person]

    return out