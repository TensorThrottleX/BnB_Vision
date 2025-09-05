import re
from dataclasses import dataclass, field
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

INSIDE_AIRBNB_INDEX = "https://insideairbnb.com/get-the-data/"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://insideairbnb.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

LISTING_SUFFIX = "listings.csv.gz"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

@dataclass
class DatasetVersion:
    date: str
    listings_url: str
    reviews_url: str
    neighbourhoods_url: str
    neighbourhoods_geojson_url: str

@dataclass
class CityCatalog:
    latest_date: str
    versions: Dict[str, DatasetVersion] = field(default_factory=dict)

CatalogType = Dict[str, Dict[str, Dict[str, CityCatalog]]]

def _fetch_index() -> str:
    r = requests.get(INSIDE_AIRBNB_INDEX, headers=HEADERS, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Index fetch failed HTTP {r.status_code}")
    return r.text

def _extract_listing_links(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.endswith(LISTING_SUFFIX):
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = "https://insideairbnb.com" + href
            links.append(href)
    return list(set(links))

def _parse(url: str):
    # Expected: .../{country}/{region...}/{city}/{date}/data/listings.csv.gz
    try:
        path = url.split("://", 1)[1]
        path = path.split("/", 1)[1]
    except Exception:
        return None
    parts = path.strip("/").split("/")
    if len(parts) < 6 or parts[-1] != LISTING_SUFFIX or parts[-2] != "data":
        return None
    date = parts[-3]
    if not DATE_RE.match(date):
        return None
    city = parts[-4]
    country = parts[0]
    region_segments = parts[1:-4]
    region = "/".join(region_segments) if region_segments else "_"
    return country, region, city, date

def scrape_catalog() -> CatalogType:
    html = _fetch_index()
    links = _extract_listing_links(html)
    catalog: CatalogType = {}
    for link in links:
        parsed = _parse(link)
        if not parsed:
            continue
        country, region, city, date = parsed
        base = link.rsplit("data/listings.csv.gz", 1)[0]
        version = DatasetVersion(
            date=date,
            listings_url=link,
            reviews_url=base + "data/reviews.csv.gz",
            neighbourhoods_url=base + "visualisations/neighbourhoods.csv",
            neighbourhoods_geojson_url=base + "visualisations/neighbourhoods.geojson",
        )
        city_entry = catalog.setdefault(country, {}).setdefault(region, {}).setdefault(
            city, CityCatalog(latest_date=date, versions={})
        )
        city_entry.versions[date] = version
        if date > city_entry.latest_date:
            city_entry.latest_date = date
    return catalog