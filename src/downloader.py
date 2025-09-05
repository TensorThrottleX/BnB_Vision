from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import time
import random
import requests
from src.scraper import DatasetVersion, HEADERS  # existing scraper module

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

MIN_VALID_SIZE_BYTES = 8_000  # avoid tiny HTML 403 pages
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.1 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "DNT": "1",
}

session = requests.Session()
session.headers.update(HEADERS)

def _is_gzip(b: bytes) -> bool:
    return len(b) >= 2 and b[0] == 0x1F and b[1] == 0x8B

def _save_file(city: str, date: str, base: str, suffix: str, data: bytes) -> Path:
    p = RAW_DIR / f"{city}_{date}_{base}{suffix}"
    p.write_bytes(data)
    return p

def _fetch(url: str, timeout: int = 90):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        return r.status_code, r.content, dict(r.headers)
    except requests.RequestException:
        return 0, b"", {}

def _try_download(url: str, expect_gzip: bool, city: str, date: str, base_name: str):
    status, data, _ = _fetch(url)
    note = f"http {status}, {len(data)} bytes"
    if status != 200 or len(data) < MIN_VALID_SIZE_BYTES:
        return None, note
    if expect_gzip and _is_gzip(data):
        return _save_file(city, date, base_name, ".csv.gz", data), f"{note} (gz)"
    if url.endswith(".csv"):
        return _save_file(city, date, base_name, ".csv", data), note
    if expect_gzip and not _is_gzip(data):
        # fallback treat as plain
        return _save_file(city, date, base_name, ".csv", data), f"{note} (plain)"
    if url.endswith(".geojson"):
        return _save_file(city, date, base_name, ".geojson", data), note
    return _save_file(city, date, base_name, ".dat", data), note

def _cached_file(city: str, date: str, base: str) -> Optional[Path]:
    for suf in (".csv.gz", ".csv"):
        p = RAW_DIR / f"{city}_{date}_{base}{suf}"
        if p.exists() and p.stat().st_size >= MIN_VALID_SIZE_BYTES:
            return p
    return None

def download_dataset(
    version: DatasetVersion,
    city: str,
    date: str,
    force: bool = False,
    override_listings_url: Optional[str] = None,
    allow_cached_if_blocked: bool = True,
    max_retries: int = 4,
    backoff_base: float = 1.2
) -> Dict[str, Optional[Path]]:
    """
    Enhanced dataset downloader with:
      - Rotating User-Agent & retry
      - Override URL support
      - Fallback to cached even when force=True (if allow_cached_if_blocked)
    Returns dict with keys: listings, reviews, neighbourhoods, status_info, blocked
    """
    attempts = []
    blocked = False
    out: Dict[str, Optional[Path]] = {
        "listings": None,
        "reviews": None,
        "neighbourhoods": None,
        "status_info": None,
        "blocked": None
    }

    def record(label: str, msg: str):
        attempts.append((label, msg))

    def rotate_headers():
        session.headers.update({**BASE_HEADERS, "User-Agent": random.choice(USER_AGENTS)})

    def try_retries(label: str, url: str, expect_gzip: bool, base_name: str):
        nonlocal blocked
        for attempt in range(1, max_retries + 1):
            rotate_headers()
            f, note = _try_download(url, expect_gzip, city, date, base_name)
            record(f"{label}-try{attempt}", note)
            if f:
                return f
            if "http 403" in note:
                blocked = True
            time.sleep((backoff_base ** (attempt - 1)) + random.uniform(0, 0.4))
        return None

    # Build listing url candidates
    listings_urls = []
    if override_listings_url:
        listings_urls.append(("override", override_listings_url, override_listings_url.endswith(".gz")))
    else:
        if version.listings_url:
            listings_urls.append(("primary", version.listings_url, True))
            if version.listings_url.endswith(".csv.gz"):
                listings_urls.append(("alt", version.listings_url.replace(".csv.gz", ".csv"), False))

    cached_before = None if force else _cached_file(city, date, "listings")

    # Attempt
    for lbl, url, gz in listings_urls:
        out["listings"] = try_retries(f"listings-{lbl}", url, gz, "listings")
        if out["listings"]:
            break

    # Fallback to cache
    if not out["listings"]:
        cached_anyway = _cached_file(city, date, "listings")
        if cached_anyway and allow_cached_if_blocked:
            out["listings"] = cached_anyway
            record("listings-cache-fallback", f"used {cached_anyway.name}")

    # Reviews & neighbourhoods best-effort
    if version.reviews_url:
        out["reviews"] = try_retries("reviews", version.reviews_url, True, "reviews")
    if version.neighbourhoods_url:
        out["neighbourhoods"] = try_retries("neighbourhoods", version.neighbourhoods_url, False, "neighbourhoods")
    elif version.neighbourhoods_geojson_url:
        out["neighbourhoods"] = try_retries("neigh-geojson", version.neighbourhoods_geojson_url, False, "neighbourhoods")

    out["status_info"] = attempts
    out["blocked"] = blocked

    if not out["listings"]:
        reasons = "\n".join(f"- {lab}: {msg}" for lab, msg in attempts)
        raise RuntimeError(
            "Listings file could not be fetched.\nTried:\n"
            f"{reasons}\nHints:\n"
            "1. Check network / VPN.\n"
            "2. City/date may have been removed.\n"
            "3. Try another date or override URL.\n"
            "4. Use Manual Upload or Direct CSV URL mode.\n"
        )
    return out