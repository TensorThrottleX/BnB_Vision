from __future__ import annotations
import requests
from typing import Tuple, Dict

def fetch(url: str, timeout: int = 60) -> Tuple[int, bytes, Dict[str, str]]:
    r = requests.get(url, timeout=timeout)
    return r.status_code, r.content, dict(r.headers)