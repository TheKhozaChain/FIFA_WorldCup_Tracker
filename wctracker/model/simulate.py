"""Monte Carlo simulation of the remaining group stage.

Goal sampling is vectorised with numpy (fast); the WC2026 advancement rules are
then resolved per simulation so the **official within-group tie-breakers** apply
— points, then head-to-head among teams level on points, then overall goal
difference / goals scored, then FIFA ranking (see `order_group_h2h`). Getting
head-to-head right matters: under 2026 rules it outranks goal difference, which
can decide who takes third place (and therefore who is eliminated). The eight
best third-placed teams are then compared across groups on points → GD → goals
scored (no head-to-head across groups).
"""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from ..types import Tournament
from .standings import apply_match, build_records, order_group_h2h
from .strength import expected_goals, load_ratings, rating_of
from .tiebreak import BEST_THIRDS_ADVANCING

_Rec = namedtuple("_Rec", "team points gd gf")


@dataclass
class SimulationResult:
    probabilities: Dict[str, float]   # team -> P(advance)
    n_sims: int


def simulate(
    tournament: Tournament,
    n_sims: int = 10_000,
    seed: int | None = None,
    home_advantage: float | None = None,
    ratings: Dict[str, float] | None = None,
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    ratings = ratings or load_ratings()

    teams = tournament.teams()
    idx = {team: i for i, team in enumerate(teams)}
    n_teams = len(teams)
    # ratings keyed by team index, for the in-loop FIFA-ranking tie-break
    rating_by_id = {i: rating_of(ratings, t) for t, i in idx.items()}

    pts, gf, ga = _base_arrays(tournament, teams, idx)
    pts = np.tile(pts, (n_sims, 1)).astype(np.int64)
    gf = np.tile(gf, (n_sims, 1)).astype(np.int64)
    ga = np.tile(ga, (n_sims, 1)).astype(np.int64)

    # Per remaining fixture, keep the sampled scorelines so head-to-head can be
    # reconstructed per simulation; also fold them into the running totals.
    sampled = _play_remaining(tournament, idx, pts, gf, ga, rng,
                              home_advantage, ratings, n_sims)

    # Lists are markedly faster than numpy scalar indexing in the per-sim loop.
    pts_l, gf_l, ga_l = pts.tolist(), gf.tolist(), ga.tolist()
    group_matches = _group_match_plan(tournament, idx, sampled)

    counts = _resolve_all(
        n_sims, n_teams, tournament, idx, pts_l, gf_l, ga_l,
        group_matches, rating_by_id,
    )

    probs = {team: counts[i] / n_sims for team, i in idx.items()}
    return SimulationResult(probabilities=probs, n_sims=n_sims)


def _base_arrays(tournament: Tournament, teams: List[str], idx: Dict[str, int]):
    """Points / goals-for / goals-against from *played* matches only."""
    records = build_records(tournament)
    for match in tournament.matches:
        apply_match(records, match)
    n = len(teams)
    pts = np.zeros(n, dtype=np.int64)
    gf = np.zeros(n, dtype=np.int64)
    ga = np.zeros(n, dtype=np.int64)
    for team, i in idx.items():
        r = records[team]
        pts[i], gf[i], ga[i] = r.points, r.gf, r.ga
    return pts, gf, ga


def _play_remaining(tournament, idx, pts, gf, ga, rng, home_advantage, ratings, n_sims):
    """Sample every unplayed fixture, fold it into the totals, and return the
    sampled scorelines as {match_key: (home_goals_list, away_goals_list)}."""
    sampled = {}
    kwargs = {} if home_advantage is None else {"home_advantage": home_advantage}
    for k, m in enumerate(tournament.matches):
        if m.played:
            continue
        h, a = idx[m.home], idx[m.away]
        lam_h, lam_a = expected_goals(
            rating_of(ratings, m.home), rating_of(ratings, m.away), **kwargs
        )
        hg = rng.poisson(lam_h, size=n_sims)
        ag = rng.poisson(lam_a, size=n_sims)
        home_win = hg > ag
        away_win = ag > hg
        draw = hg == ag
        pts[:, h] += 3 * home_win + draw
        pts[:, a] += 3 * away_win + draw
        gf[:, h] += hg
        ga[:, h] += ag
        gf[:, a] += ag
        ga[:, a] += hg
        sampled[k] = (hg.tolist(), ag.tolist())
    return sampled


def _group_match_plan(tournament, idx, sampled):
    """Per group, the list of resolved matches as (home_idx, away_idx, source).

    `source` is either ("played", hg, ag) or ("sim", home_goals_list,
    away_goals_list) so the per-sim loop can read each scoreline cheaply."""
    plan = {g: [] for g in tournament.groups}
    for k, m in enumerate(tournament.matches):
        h, a = idx[m.home], idx[m.away]
        if m.played:
            plan[m.group].append((h, a, ("played", m.home_goals, m.away_goals)))
        else:
            hg, ag = sampled[k]
            plan[m.group].append((h, a, ("sim", hg, ag)))
    return plan


def _resolve_all(n_sims, n_teams, tournament, idx, pts_l, gf_l, ga_l,
                 group_matches, rating_by_id):
    """Resolve advancement for every simulation; return per-team advance counts."""
    counts = [0] * n_teams
    group_members = {g: [idx[t] for t in teams]
                     for g, teams in tournament.groups.items()}

    for s in range(n_sims):
        prow, gfrow, garow = pts_l[s], gf_l[s], ga_l[s]
        thirds = []  # (team_id, points, gd, gf) of each group's third-placed team
        for group, members in group_members.items():
            recs = [_Rec(t, prow[t], gfrow[t] - garow[t], gfrow[t]) for t in members]
            results = [
                (h, a, src[1] if src[0] == "played" else src[1][s],
                       src[2] if src[0] == "played" else src[2][s])
                for h, a, src in group_matches[group]
            ]
            order = order_group_h2h(recs, results, rating_by_id)
            counts[order[0].team] += 1
            counts[order[1].team] += 1
            t3 = order[2]
            thirds.append((t3.team, t3.points, t3.gd, t3.gf))

        # Eight best third-placed teams: points -> GD -> goals -> FIFA ranking.
        thirds.sort(key=lambda x: (x[1], x[2], x[3], rating_by_id[x[0]]), reverse=True)
        for t in thirds[:BEST_THIRDS_ADVANCING]:
            counts[t[0]] += 1

    return counts
