"""Local file cache so ordinary re-runs never touch the network.

A fetched `Tournament` is serialised to `data/cache/<provider>.json`. The CLI
reads the cache unless it is missing, older than the TTL, or `--refresh` is
passed. This is what keeps us comfortably inside a 10-req/min free tier.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from ..types import Match, Tournament

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour


def _path(provider: str) -> Path:
    return CACHE_DIR / f"{provider}.json"


def save(provider: str, tournament: Tournament) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "groups": tournament.groups,
        "matches": [asdict(m) for m in tournament.matches],
        "fetched_at": tournament.fetched_at,
        "source": tournament.source,
        "cached_at": time.time(),
    }
    path = _path(provider)
    path.write_text(json.dumps(payload, indent=2))
    return path


def load(provider: str, ttl: int = DEFAULT_TTL_SECONDS) -> Optional[Tournament]:
    """Return the cached tournament if present and fresh, else None."""
    path = _path(provider)
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    if ttl >= 0 and (time.time() - payload.get("cached_at", 0)) > ttl:
        return None
    return _deserialise(payload)


def _deserialise(payload: dict) -> Tournament:
    matches = [
        Match(
            group=m["group"],
            home=m["home"],
            away=m["away"],
            home_goals=m["home_goals"],
            away_goals=m["away_goals"],
            played=m["played"],
        )
        for m in payload["matches"]
    ]
    return Tournament(
        groups=payload["groups"],
        matches=matches,
        fetched_at=payload.get("fetched_at", ""),
        source=payload.get("source", ""),
    )
