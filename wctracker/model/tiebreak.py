"""Group ranking and the best-third-placed cross-group comparison.

The 8-best-third-placed rule is the single trickiest part of the WC2026 format:
the third-placed team in Group A is compared directly against the third-placed
team in Group L even though they never met. Per the FIFA rules the comparison
is on points, then goal difference, then goals scored (there is no head-to-head
across groups). This module is pure and deterministic so it can be tested hard.
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

from ..types import TeamRecord
from .standings import order_group

#: number of third-placed teams that advance to the knockout round
BEST_THIRDS_ADVANCING = 8


def is_eliminated_from_group(
    team: str,
    group_records: List[TeamRecord],
    played_results: List[Tuple[str, str, int, int]],
    remaining: List[Tuple[str, str]],
) -> bool:
    """Return True if `team` is **mathematically eliminated**.

    A team advances only if it finishes in the top two of its group or as one of
    the eight best third-placed teams — so a team that can no longer reach even
    *third* place is out, no cross-group analysis required.

    We enumerate every win/draw/loss combination of the group's remaining
    fixtures and ask whether `team` can still finish in the top three. Crucially,
    this honours the WC2026 rule that **head-to-head is decided before goal
    difference**: a rival level on points that has already beaten `team` is
    counted as finishing above it. The check is *sound* — it only declares
    elimination when no surviving scenario exists (multi-way point ties are left
    in the team's favour), so it never eliminates a team prematurely.
    """
    current = {r.team: r.points for r in group_records}
    others = [t for t in current if t != team]

    h2h_base = {}
    for home, away, hg, ag in played_results:
        h2h_base[frozenset((home, away))] = home if hg > ag else (away if ag > hg else None)

    # home pts, away pts, winning side for each possible match outcome
    outcomes = ((3, 0, "h"), (1, 1, None), (0, 3, "a"))
    for combo in itertools.product(outcomes, repeat=len(remaining)):
        pts = dict(current)
        h2h = dict(h2h_base)
        for (home, away), (hp, ap, side) in zip(remaining, combo):
            pts[home] += hp
            pts[away] += ap
            h2h[frozenset((home, away))] = home if side == "h" else (away if side == "a" else None)

        tp = pts[team]
        above = sum(1 for r in others if pts[r] > tp)
        level = [r for r in others if pts[r] == tp]
        # A single rival level on points that won the head-to-head finishes above.
        if len(level) == 1 and h2h.get(frozenset((level[0], team))) == level[0]:
            above += 1
        if above <= 2:           # third place (or better) is still reachable
            return False
    return True


def group_qualifiers(ordered_group: List[TeamRecord]) -> List[TeamRecord]:
    """Top two of an already-ordered group qualify automatically."""
    return ordered_group[:2]


def third_placed(ordered_group: List[TeamRecord]) -> TeamRecord:
    """The third-placed team of an already-ordered group."""
    return ordered_group[2]


def rank_best_thirds(thirds: List[TeamRecord]) -> List[TeamRecord]:
    """Order every group's third-placed team best-first.

    Comparison key: points, then goal difference, then goals scored. Residual
    ties fall back to team name so the output is deterministic (the real
    competition would use drawing of lots; the simulation injects randomness
    instead — see simulate.py)."""
    return order_group(thirds)


def best_thirds_advancing(
    thirds: List[TeamRecord],
    n: int = BEST_THIRDS_ADVANCING,
) -> List[TeamRecord]:
    """Return the `n` third-placed teams that advance."""
    return rank_best_thirds(thirds)[:n]


def qualified_teams(standings: Dict[str, List[TeamRecord]]) -> List[str]:
    """Full set of advancing teams: top two of each group plus the best thirds.

    `standings` must already be ordered per group (as produced by
    `compute_standings`)."""
    advancing: List[str] = []
    thirds: List[TeamRecord] = []
    for ordered in standings.values():
        advancing.extend(r.team for r in group_qualifiers(ordered))
        thirds.append(third_placed(ordered))
    advancing.extend(r.team for r in best_thirds_advancing(thirds))
    return advancing
