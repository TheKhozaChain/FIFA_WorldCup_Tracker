"""Report assembly: turn probabilities + standings into sortable rows that the
terminal table, the markdown writer, and the commentary all render."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..types import TeamRecord, Tournament

# Status values a team can hold this run.
QUALIFIED = "qualified"      # advances in every simulation (model-certain)
ELIMINATED = "eliminated"    # advances in no simulation
LIVE = "live"                # still in contention


@dataclass
class Row:
    team: str
    group: str
    start: Optional[float]   # pre-tournament %  (None if not in baseline)
    now: float               # current %
    position: int            # live group position, 1-4
    points: int = 0
    gd: int = 0
    played: int = 0
    remaining: int = 0       # group games this team has left
    won_group: bool = False  # has mathematically clinched top spot (on points)
    status: str = LIVE

    @property
    def delta(self) -> Optional[float]:
        if self.start is None:
            return None
        return self.now - self.start


def status_of(prob: float) -> str:
    """Classify a team from its advancement probability (0..1). Exact 1.0/0.0
    mean every / no simulation advanced them — certain within the model."""
    if prob >= 1.0:
        return QUALIFIED
    if prob <= 0.0:
        return ELIMINATED
    return LIVE


def _group_winners(standings: Dict[str, List[TeamRecord]],
                   remaining: Dict[str, int]) -> set:
    """Teams that have clinched first place on points (strictly out of reach of
    every rival's maximum possible points)."""
    winners = set()
    for ordered in standings.values():
        if not ordered:
            continue
        leader = ordered[0]
        if all(leader.points > r.points + 3 * remaining.get(r.team, 0)
               for r in ordered[1:]):
            winners.add(leader.team)
    return winners


def build_rows(
    tournament: Tournament,
    now_probs: Dict[str, float],
    baseline: Dict[str, float],
    standings: Dict[str, List[TeamRecord]],
    remaining: Dict[str, int],
    eliminated: set | None = None,
) -> List[Row]:
    eliminated = eliminated or set()
    position: Dict[str, int] = {}
    record: Dict[str, TeamRecord] = {}
    for ordered in standings.values():
        for i, rec in enumerate(ordered, start=1):
            position[rec.team] = i
            record[rec.team] = rec
    winners = _group_winners(standings, remaining)

    rows = []
    for team in tournament.teams():
        rec = record.get(team)
        # A deterministic mathematical elimination overrides the simulation: a
        # team that cannot reach third place is out even if random noise in the
        # sim ever showed otherwise.
        status = ELIMINATED if team in eliminated else status_of(now_probs[team])
        rows.append(Row(
            team=team,
            group=tournament.group_of(team) or "?",
            start=baseline.get(team),
            now=now_probs[team] * 100.0,
            position=position.get(team, 0),
            points=rec.points if rec else 0,
            gd=rec.gd if rec else 0,
            played=rec.played if rec else 0,
            remaining=remaining.get(team, 0),
            won_group=team in winners,
            status=status,
        ))
    # Sort by Δ descending; teams without a baseline (Δ None) sort to the end.
    rows.sort(key=lambda r: (r.delta is not None, r.delta if r.delta is not None else 0.0,
                             r.now), reverse=True)
    return rows
