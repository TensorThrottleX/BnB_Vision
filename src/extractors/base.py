from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ExtractionResult:
    def __init__(self, records: List[Dict[str, Any]], meta: Dict[str, Any]):
        self.records = records
        self.meta = meta

class BaseExtractor(ABC):
    name: str = "base"

    @abstractmethod
    def can_handle(self, url: str, html_text: str | None = None) -> bool:
        ...

    @abstractmethod
    def extract(self, url: str, html_text: str) -> ExtractionResult:
        ...