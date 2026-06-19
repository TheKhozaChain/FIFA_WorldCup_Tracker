"""Offline provider: builds a `Tournament` from the bundled snapshot.

The snapshot (`wctracker/data/snapshot.json`) is a curated copy of the real
group-stage state — groups, played results, and remaining fixtures — frozen at
`fetched_at`. It lets the tool run with no API key or network, and is the
fixture the tests rely on. Because it is frozen, it goes stale: use a live
provider for up-to-the-minute numbers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ..types import Match, Tournament
from .base import DataProvider, ProviderError

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "snapshot.json"


class OfflineProvider(DataProvider):
    name = "offline"

    def __init__(self, snapshot_path: Optional[Path] = None) -> None:
        self.snapshot_path = snapshot_path or SNAPSHOT_PATH

    def fetch(self) -> Tournament:
        if not self.snapshot_path.exists():
            raise ProviderError(f"snapshot not found at {self.snapshot_path}")
        data = json.loads(self.snapshot_path.read_text())
        return tournament_from_snapshot(data, source=self.name)


def tournament_from_snapshot(data: dict, source: str = "offline") -> Tournament:
    """Read a {groups, matches} snapshot into a `Tournament`."""
    matches: List[Match] = []
    for m in data["matches"]:
        played = bool(m.get("played", False))
        matches.append(
            Match(
                group=m["group"],
                home=m["home"],
                away=m["away"],
                home_goals=m["home_goals"] if played else None,
                away_goals=m["away_goals"] if played else None,
                played=played,
            )
        )
    return Tournament(
        groups=data["groups"],
        matches=matches,
        fetched_at=data.get("fetched_at", ""),
        source=source,
    )
