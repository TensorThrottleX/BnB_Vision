from pathlib import Path
import joblib
from datetime import datetime

def save_model(model, city: str, date: str, models_dir: Path = Path("models")) -> Path:
    models_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = models_dir / f"{city}_{date}_{ts}_model.joblib"
    joblib.dump(model, path)
    return path