"""Report assembly: turn probabilities + baseline into sortable rows that both
the terminal table and the markdown writer render."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..types import Tournament


@dataclass
class Row:
    team: str
    group: str
    start: Optional[float]   # pre-tournament %  (None if not in baseline)
    now: float               # current %
    position: int            # live group position, 1-4 (for context)

    @property
    def delta(self) -> Optional[float]:
        if self.start is None:
            return None
        return self.now - self.start


def build_rows(
    tournament: Tournament,
    now_probs: Dict[str, float],
    baseline: Dict[str, float],
    positions: Dict[str, int],
) -> List[Row]:
    rows = [
        Row(
            team=team,
            group=tournament.group_of(team) or "?",
            start=baseline.get(team),
            now=now_probs[team] * 100.0,
            position=positions.get(team, 0),
        )
        for team in tournament.teams()
    ]
    # Sort by Δ descending; teams without a baseline (Δ None) sort to the end.
    rows.sort(key=lambda r: (r.delta is not None, r.delta if r.delta is not None else 0.0,
                             r.now), reverse=True)
    return rows
