from __future__ import annotations
from .base import BaseExtractor, ExtractionResult
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from collections import Counter

PRICE_PATTERN = re.compile(r"(?:[$€£]|USD|EUR|GBP)\s?\d{1,6}(?:[.,]\d{2})?|\d{1,6}\s?(?:USD|EUR|GBP)", re.IGNORECASE)
RATING_PATTERN = re.compile(r"\b\d(?:\.\d)?\b")

class RepeatingBlockExtractor(BaseExtractor):
    name = "heuristic_blocks"

    def can_handle(self, url: str, html_text: str | None = None) -> bool:
        return True  # Fallback always tries

    def extract(self, url: str, html_text: str) -> ExtractionResult:
        soup = BeautifulSoup(html_text, "lxml")
        price_nodes = []
        for node in soup.find_all(text=PRICE_PATTERN):
            parent = node.parent
            for _ in range(4):
                if parent is None:
                    break
                if len(list(parent.children)) > 2:
                    price_nodes.append(parent)
                parent = parent.parent

        if not price_nodes:
            return ExtractionResult(records=[], meta={"matched_price_nodes": 0})

        sigs = [self.signature(el) for el in price_nodes]
        freq = Counter(sigs)
        common_sigs = [sig for sig, _ in freq.most_common(4)]

        records: List[Dict[str, Any]] = []
        seen_links = set()

        for sig in common_sigs:
            for el in soup.find_all():
                if self.signature(el) != sig:
                    continue
                text = el.get_text(" ", strip=True)
                price_match = PRICE_PATTERN.search(text)
                rating_match = RATING_PATTERN.search(text)
                link_tag = el.find("a", href=True)
                link = link_tag["href"] if link_tag else url
                if not link.startswith("http"):
                    # Not resolving relative links here—could be added if needed.
                    pass
                title = None
                for tag_name in ["h1", "h2", "h3", "h4"]:
                    t = el.find(tag_name)
                    if t and t.get_text(strip=True):
                        title = t.get_text(strip=True)
                        break
                if not title:
                    # Trim to snippet
                    title = text[:120]
                if link in seen_links:
                    continue
                seen_links.add(link)
                records.append({
                    "source": "heuristic",
                    "title": title,
                    "url": link,
                    "raw_price": price_match.group(0) if price_match else None,
                    "raw_rating": rating_match.group(0) if rating_match else None
                })

        meta = {
            "extractor": self.name,
            "price_nodes_examined": len(price_nodes),
            "signatures_considered": freq.most_common(6),
            "records": len(records)
        }
        return ExtractionResult(records=records, meta=meta)

    def signature(self, el) -> str:
        if not hasattr(el, "name") or el.name is None:
            return "none"
        classes = "-".join(sorted(el.get("class", [])))
        child_count = sum(1 for c in el.find_all(recursive=False) if getattr(c, "name", None))
        return f"{el.name}|{classes}|{child_count}"