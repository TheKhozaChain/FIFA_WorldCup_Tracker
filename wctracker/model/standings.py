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


def compute_standings(
    tournament: Tournament,
    ratings: Dict[str, float] | None = None,
) -> Dict[str, List[TeamRecord]]:
    """Return ordered standings per group: {group_letter: [1st, 2nd, 3rd, 4th]}.

    Ordering follows the official **WC2026** group order (see `order_group_h2h`):
    points, then head-to-head among teams level on points, then overall goal
    difference / goals scored, then FIFA ranking (approximated by `ratings`).
    """
    records = build_records(tournament)
    for match in tournament.matches:
        apply_match(records, match)

    standings: Dict[str, List[TeamRecord]] = {}
    for group, teams in tournament.groups.items():
        group_records = [records[t] for t in teams]
        results = [
            (m.home, m.away, m.home_goals, m.away_goals)
            for m in tournament.matches
            if m.played and m.group == group
        ]
        standings[group] = order_group_h2h(group_records, results, ratings)
    return standings


def order_group(records: Iterable[TeamRecord]) -> List[TeamRecord]:
    """Sort best-first by points, GD, goals scored, then team name.

    Used for the **cross-group** best-third comparison, where head-to-head does
    not apply (the teams never met)."""
    return sorted(
        records,
        key=lambda r: (r.points, r.gd, r.gf, _name_key(r.team)),
        reverse=True,
    )


def order_group_h2h(
    records: Iterable,
    results: Iterable,
    ratings: Dict | None = None,
    default_rating: float = 1500.0,
) -> List:
    """Order one group best-first under the **WC2026 within-group rules**:

      1. points
      2. head-to-head among teams level on points: points, then goal
         difference, then goals scored *in the matches between them*
      3. overall goal difference, then overall goals scored
      4. FIFA ranking (approximated here by `ratings`)

    `records` need `.team`, `.points`, `.gd`, `.gf`; `results` are
    `(home, away, home_goals, away_goals)` tuples for the group's resolved
    matches. (Head-to-head is applied as a single mini-table pass — a documented
    simplification of the rare recursive "re-apply after partial separation"
    case; see docs/methodology.md.)
    """
    ratings = ratings or {}

    def rating_of(team):
        return ratings.get(team, ratings.get("__default__", default_rating))

    recs = sorted(records, key=lambda r: r.team)          # stable A→Z / id base
    recs.sort(key=lambda r: r.points, reverse=True)        # then by points

    ordered: List = []
    i, n = 0, len(recs)
    while i < n:
        j = i
        while j < n and recs[j].points == recs[i].points:
            j += 1
        cluster = recs[i:j]
        if len(cluster) == 1:
            ordered.extend(cluster)
        else:
            ordered.extend(_resolve_tie(cluster, list(results), rating_of))
        i = j
    return ordered


def _resolve_tie(cluster: List, results: List, rating_of) -> List:
    """Order teams that are level on points using the head-to-head mini-table,
    then overall GD / goals, then rating."""
    names = {r.team for r in cluster}
    mini = {r.team: [0, 0, 0] for r in cluster}   # [h2h points, h2h GD, h2h GF]
    for home, away, hg, ag in results:
        if home in names and away in names:
            mini[home][1] += hg - ag
            mini[home][2] += hg
            mini[away][1] += ag - hg
            mini[away][2] += ag
            if hg > ag:
                mini[home][0] += 3
            elif ag > hg:
                mini[away][0] += 3
            else:
                mini[home][0] += 1
                mini[away][0] += 1

    def key(r):
        m = mini[r.team]
        return (m[0], m[1], m[2], r.gd, r.gf, rating_of(r.team))

    # reverse=True ranks the key descending; teams identical on every criterion
    # keep the cluster's existing A→Z / id order (stable sort).
    return sorted(cluster, key=key, reverse=True)


def _name_key(name: str) -> tuple:
    """Make alphabetical order sort *consistently* under reverse=True so the
    deterministic fallback is A→Z, not Z→A."""
    return tuple(-ord(c) for c in name)
