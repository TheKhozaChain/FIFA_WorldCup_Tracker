"""Load the frozen pre-tournament baseline probabilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

BASELINE_PATH = Path(__file__).resolve().parent.parent / "data" / "baseline.json"


def load_baseline(path: Path | None = None) -> Dict[str, float]:
    """Return {team: start_percent}. Empty dict if the file is missing."""
    path = path or BASELINE_PATH
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return {t: float(p) for t, p in payload.get("probabilities", {}).items()}
