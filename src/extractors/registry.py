from __future__ import annotations
from typing import List
from .base import BaseExtractor
from .airbnb_stub import AirbnbStubExtractor
from .generic_structured import StructuredDataExtractor
from .generic_repeating import RepeatingBlockExtractor

# Ordered priority: specialized -> structured -> heuristic fallback
_EXTRACTORS: List[BaseExtractor] = [
    AirbnbStubExtractor(),
    StructuredDataExtractor(),
    RepeatingBlockExtractor()
]

def get_extractors() -> List[BaseExtractor]:
    return _EXTRACTORS[:]