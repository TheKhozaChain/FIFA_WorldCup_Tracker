"""Offline provider: builds a `Tournament` from the bundled snapshot.

This is what makes the tool runnable with no API key and no network — and it
is also the fixture every test relies on. The snapshot stores group line-ups
plus whatever results have been "played"; the full 6-match-per-group fixture
list is generated from the round-robin schedule, and any fixture with a stored
result is marked played.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..fixtures import round_robin
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
    """Expand a {groups, results} snapshot into a full `Tournament`."""
    groups: Dict[str, List[str]] = data["groups"]
    results = _index_results(data.get("results", []))

    matches: List[Match] = []
    for group, teams in groups.items():
        for home, away in round_robin(teams):
            score = results.get((group, home, away))
            if score is not None:
                matches.append(
                    Match(group, home, away, score[0], score[1], played=True)
                )
            else:
                matches.append(Match(group, home, away, played=False))

    return Tournament(
        groups=groups,
        matches=matches,
        fetched_at=data.get("fetched_at", ""),
        source=source,
    )


def _index_results(results: List[dict]) -> Dict[Tuple[str, str, str], Tuple[int, int]]:
    indexed: Dict[Tuple[str, str, str], Tuple[int, int]] = {}
    for r in results:
        indexed[(r["group"], r["home"], r["away"])] = (
            int(r["home_goals"]),
            int(r["away_goals"]),
        )
    return indexed
