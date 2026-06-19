"""Group ranking and the best-third-placed cross-group comparison.

The 8-best-third-placed rule is the single trickiest part of the WC2026 format:
the third-placed team in Group A is compared directly against the third-placed
team in Group L even though they never met. Per the FIFA rules the comparison
is on points, then goal difference, then goals scored (there is no head-to-head
across groups). This module is pure and deterministic so it can be tested hard.
"""
from __future__ import annotations

from typing import Dict, List

from ..types import TeamRecord
from .standings import order_group

#: number of third-placed teams that advance to the knockout round
BEST_THIRDS_ADVANCING = 8


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
