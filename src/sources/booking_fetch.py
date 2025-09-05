from __future__ import annotations
import requests, time, random, json, os, hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from bs4 import BeautifulSoup
from datetime import datetime

ESSENTIAL_PARAMS = {"checkin", "checkout", "dest_id", "dest_type", "city"}
PAGE_SIZE = 25

class BookingBlocked(Exception):
    pass

def normalize_booking_url(raw: str) -> str:
    p = urlparse(raw)
    qs = parse_qs(p.query)
    filtered = {}
    for k, v in qs.items():
        if k.lower() in ESSENTIAL_PARAMS:
            filtered[k] = v
    new_q = urlencode(filtered, doseq=True)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, new_q, ""))

def _manifest_path(cache_dir: str, key: str) -> str:
    return os.path.join(cache_dir, f"{key}.meta.json")

def _data_path(cache_dir: str, key: str) -> str:
    return os.path.join(cache_dir, f"{key}.listings.json")

def fetch_booking_listings(url: str, pages: int = 2, delay: float = 0.8,
                           cache_dir: str = "src\\manifests",
                           force_refresh: bool = False):
    os.makedirs(cache_dir, exist_ok=True)
    norm = normalize_booking_url(url)
    key = "booking_" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
    manifest_file = _manifest_path(cache_dir, key)
    data_file = _data_path(cache_dir, key)

    if (not force_refresh) and os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload, manifest_file

    session = requests.Session()
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml"
    }

    all_rows = []
    blocked = False
    statuses = []

    for page in range(pages):
        offset = page * PAGE_SIZE
        page_url = norm
        if offset:
            sep = "&" if "?" in page_url else "?"
            page_url = f"{norm}{sep}offset={offset}"

        r = session.get(page_url, headers=headers, timeout=30)
        statuses.append({"url": page_url, "status": r.status_code})
        if r.status_code in (403, 429):
            blocked = True
            break
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select('[data-testid="property-card"]')
        if not cards:
            break
        for card in cards:
            title_tag = card.select_one('a[data-testid="title-link"]')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            rel = title_tag.get("href") or ""
            full = urljoin("https://www.booking.com", rel.split("?")[0])
            price_el = card.select_one('[data-testid="price-and-discounted-price"]')
            price_txt = price_el.get_text(" ", strip=True) if price_el else ""
            all_rows.append({
                "source": "booking",
                "title": title,
                "url": full,
                "raw_price": price_txt
            })
        time.sleep(delay + random.random()*0.3)

    if blocked:
        raise BookingBlocked(f"Blocked (statuses: {statuses})")

    manifest = {
        "source": "booking",
        "normalized_url": norm,
        "original_url_hash": hashlib.md5(url.encode("utf-8")).hexdigest(),
        "fetched_at": datetime.utcnow().isoformat(),
        "pages_attempted": pages,
        "records": len(all_rows),
        "http_trace": statuses,
        "blocked": False
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return all_rows, manifest_file