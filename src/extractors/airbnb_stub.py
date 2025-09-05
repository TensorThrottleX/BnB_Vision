from __future__ import annotations
from .base import BaseExtractor, ExtractionResult

class AirbnbStubExtractor(BaseExtractor):
    name = "airbnb_stub"

    def can_handle(self, url: str, html_text: str | None = None) -> bool:
        return "airbnb." in url.lower()

    def extract(self, url: str, html_text: str) -> ExtractionResult:
        # Placeholder - no Airbnb scraping logic included
        return ExtractionResult(
            records=[],
            meta={"note": "Airbnb extraction stub. Implement real logic if needed."}
        )