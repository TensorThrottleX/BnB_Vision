from __future__ import annotations
import re

def basic_sentiment_placeholder(text: str) -> float:
    if not text:
        return 0.5
    txt = text.lower()
    pos = len(re.findall(r"\b(good|great|nice|amazing|excellent|clean)\b", txt))
    neg = len(re.findall(r"\b(bad|dirty|poor|terrible|noisy)\b", txt))
    total = pos + neg
    if total == 0:
        return 0.5
    return max(0.0, min(1.0, pos / total))