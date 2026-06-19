"""Round-robin fixture generation for a 4-team group.

Used both to expand the offline snapshot into a full fixture list and to
build the pre-tournament baseline (where every match is unplayed). The exact
match-day ordering is cosmetic — simulation results do not depend on it.
"""
from __future__ import annotations

from typing import List, Tuple


def round_robin(teams: List[str]) -> List[Tuple[str, str]]:
    """Return the 6 (home, away) pairings for a single group of 4."""
    if len(teams) != 4:
        raise ValueError(f"a WC2026 group must have exactly 4 teams, got {len(teams)}")
    a, b, c, d = teams
    return [
        (a, b), (c, d),   # match-day 1
        (a, c), (d, b),   # match-day 2
        (d, a), (b, c),   # match-day 3
    ]
