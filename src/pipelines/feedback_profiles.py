from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path

PROFILES_DIR = Path("data/profiles")
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WEIGHTS = {
    "value": 1.0,
    "amenities": 1.0,
    "reviews": 1.0,
    "availability": 0.7
}

def profile_path(name: str) -> Path:
    safe = name.replace(" ", "_").lower()
    return PROFILES_DIR / f"{safe}.json"

def list_profiles():
    return [p.stem for p in PROFILES_DIR.glob("*.json")]

def save_profile(name: str, data: Dict[str, Any]):
    with profile_path(name).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_profile(name: str):
    p = profile_path(name)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)