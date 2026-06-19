"""Core domain types shared across providers, model, and reporting.

Keeping these as plain dataclasses (no provider-specific fields) is what lets
the data layer stay swappable: every provider must translate its own JSON into
these types, and nothing downstream knows or cares which API produced them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Match:
    """A single group-stage fixture.

    `played` is the source of truth for whether goals are real results
    (used to build current standings) or unknown (simulated).
    """
    group: str
    home: str
    away: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    played: bool = False

    def __post_init__(self) -> None:
        if self.played and (self.home_goals is None or self.away_goals is None):
            raise ValueError(
                f"played match {self.home} v {self.away} is missing a scoreline"
            )


@dataclass
class Tournament:
    """The full picture the rest of the app reasons about: who is in which
    group, and every fixture (played and not yet played)."""
    groups: Dict[str, List[str]]          # group letter -> ordered team names
    matches: List[Match]
    fetched_at: str = ""                  # ISO timestamp, for cache display
    source: str = ""                      # provider name, for provenance

    def teams(self) -> List[str]:
        return [team for teams in self.groups.values() for team in teams]

    def group_of(self, team: str) -> Optional[str]:
        for g, teams in self.groups.items():
            if team in teams:
                return g
        return None


@dataclass
class TeamRecord:
    """A team's accumulated group-stage record. Mutated while building
    standings and copied per-simulation in the Monte Carlo path."""
    team: str
    group: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    gf: int = 0          # goals for
    ga: int = 0          # goals against

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    def sort_key(self) -> tuple:
        """FIFA group ordering: points, then goal difference, then goals
        scored. Higher is better, so negate for ascending sorts."""
        return (self.points, self.gd, self.gf)
