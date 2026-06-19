"""Build group standings from a list of matches.

This is pure, deterministic, and side-effect free so it can be unit-tested in
isolation — standings bugs are exactly the kind that quietly corrupt every
downstream probability.
"""
from __future__ import annotations

from typing import Dict, Iterable, List

from ..types import Match, TeamRecord, Tournament


def build_records(tournament: Tournament) -> Dict[str, TeamRecord]:
    """One zeroed `TeamRecord` per team, keyed by team name."""
    records: Dict[str, TeamRecord] = {}
    for group, teams in tournament.groups.items():
        for team in teams:
            records[team] = TeamRecord(team=team, group=group)
    return records


def apply_match(records: Dict[str, TeamRecord], match: Match) -> None:
    """Fold a single *played* match into the running records."""
    if not match.played:
        return
    home, away = records[match.home], records[match.away]
    hg, ag = match.home_goals, match.away_goals

    home.played += 1
    away.played += 1
    home.gf += hg
    home.ga += ag
    away.gf += ag
    away.ga += hg

    if hg > ag:
        home.won += 1
        away.lost += 1
    elif hg < ag:
        away.won += 1
        home.lost += 1
    else:
        home.drawn += 1
        away.drawn += 1


def compute_standings(tournament: Tournament) -> Dict[str, List[TeamRecord]]:
    """Return ordered standings per group: {group_letter: [1st, 2nd, 3rd, 4th]}.

    Ordering is FIFA group order (points, goal difference, goals scored). Teams
    that remain exactly tied keep a stable alphabetical order here; the genuine
    random tie-break only matters inside the Monte Carlo simulation.
    """
    records = build_records(tournament)
    for match in tournament.matches:
        apply_match(records, match)

    standings: Dict[str, List[TeamRecord]] = {}
    for group, teams in tournament.groups.items():
        group_records = [records[t] for t in teams]
        standings[group] = order_group(group_records)
    return standings


def order_group(records: Iterable[TeamRecord]) -> List[TeamRecord]:
    """Sort one group's records best-first by points, GD, goals scored, then
    team name (stable, deterministic fallback)."""
    return sorted(
        records,
        key=lambda r: (r.points, r.gd, r.gf, _name_key(r.team)),
        reverse=True,
    )


def _name_key(name: str) -> tuple:
    """Make alphabetical order sort *consistently* under reverse=True so the
    deterministic fallback is A→Z, not Z→A."""
    return tuple(-ord(c) for c in name)
