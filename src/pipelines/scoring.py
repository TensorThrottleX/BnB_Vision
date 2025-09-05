from __future__ import annotations
from typing import Dict, List
import pandas as pd

def _normalize_series(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / rng

def build_dynamic_scores(
    df: pd.DataFrame,
    weights: Dict[str, float],
    blocks: List[str]
) -> pd.DataFrame:
    val_col = "value_score_raw" if "value_metrics" in blocks and "value_score_raw" in df.columns else None
    amen_col = "amenities_score_raw" if "amenities_metrics" in blocks and "amenities_score_raw" in df.columns else None
    rev_col = "review_quality_score_raw" if "review_quality" in blocks and "review_quality_score_raw" in df.columns else None
    avail_col = "availability_score_raw" if "availability_metrics" in blocks and "availability_score_raw" in df.columns else None

    component_scores = []
    if val_col:
        df["dynamic_value_score"] = _normalize_series(df[val_col]) * weights.get("value", 1.0)
        component_scores.append("dynamic_value_score")
    if amen_col:
        df["dynamic_amenities_score"] = _normalize_series(df[amen_col]) * weights.get("amenities", 1.0)
        component_scores.append("dynamic_amenities_score")
    if rev_col:
        df["dynamic_review_quality_score"] = _normalize_series(df[rev_col]) * weights.get("reviews", 1.0)
        component_scores.append("dynamic_review_quality_score")
    if avail_col:
        df["dynamic_availability_score"] = _normalize_series(df[avail_col]) * weights.get("availability", 1.0)
        component_scores.append("dynamic_availability_score")

    if component_scores:
        df["total_score_dynamic"] = df[component_scores].sum(axis=1)
        if "total_score" in df.columns:
            df["total_score"] = (df["total_score"] + df["total_score_dynamic"]) / 2.0
        else:
            df["total_score"] = df["total_score_dynamic"]
    else:
        if "total_score" not in df.columns:
            df["total_score"] = 0.0

    reasons = []
    if val_col: reasons.append("value")
    if amen_col: reasons.append("amenities")
    if rev_col: reasons.append("reviews")
    if avail_col: reasons.append("availability")
    df["recommendation_reason"] = " + ".join(reasons) if reasons else "baseline"
    return df