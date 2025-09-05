from __future__ import annotations
from typing import List, Dict, Callable
import pandas as pd
import numpy as np

def block_value_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["id", "price", "accommodates"]].copy()
    if "accommodates" in out.columns:
        out["price_per_person"] = out.apply(
            lambda r: r["price"] / r["accommodates"] if r.get("accommodates", 0) not in (0, None, np.nan) else np.nan,
            axis=1
        )
    out["value_z"] = (out["price"] - out["price"].mean()) / (out["price"].std(ddof=0) or 1)
    out["value_score_raw"] = -out["value_z"]
    return out[["id", "price_per_person", "value_z", "value_score_raw"]]

def block_amenities_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if "amenities_count" not in df.columns:
        return pd.DataFrame({"id": df["id"]})
    out = df[["id", "amenities_count"]].copy()
    out["amenities_score_raw"] = (out["amenities_count"] - out["amenities_count"].mean()) / (
        out["amenities_count"].std(ddof=0) or 1
    )
    return out

def block_review_quality(df: pd.DataFrame) -> pd.DataFrame:
    candidates = [c for c in ["review_scores_rating", "review_scores_value", "review_scores_cleanliness"] if c in df.columns]
    base_cols = ["id"] + candidates
    out = df[base_cols].copy()
    if candidates:
        out["review_quality_score_raw"] = out[candidates].mean(axis=1) / 100.0
    return out

def block_availability(df: pd.DataFrame) -> pd.DataFrame:
    if "availability_365" not in df.columns:
        return pd.DataFrame({"id": df["id"]})
    out = df[["id", "availability_365"]].copy()
    mean_av = out["availability_365"].mean()
    out["availability_dev"] = (out["availability_365"] - mean_av).abs()
    out["availability_score_raw"] = -out["availability_dev"]
    return out

AVAILABLE_BLOCKS: Dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "value_metrics": block_value_metrics,
    "amenities_metrics": block_amenities_metrics,
    "review_quality": block_review_quality,
    "availability_metrics": block_availability
}

def compute_feature_blocks(df: pd.DataFrame, selected: List[str]) -> List[pd.DataFrame]:
    outputs = []
    for blk in selected:
        func = AVAILABLE_BLOCKS.get(blk)
        if func:
            try:
                outputs.append(func(df))
            except Exception:
                pass
    return outputs