"""Monte Carlo simulation of the remaining group stage.

Fully vectorised over the N simulations with numpy: we sample a scoreline for
every unplayed fixture, fold it onto the current standings, then resolve the
WC2026 advancement rules (top two per group + the eight best third-placed
teams) for all N simulations at once. The ranking key encodes the exact FIFA
order — points, then goal difference, then goals scored — matching the pure
`tiebreak` module; residual ties are broken by a tiny per-team random jitter,
standing in for the real "drawing of lots".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from ..types import Tournament
from .standings import apply_match, build_records
from .strength import expected_goals, load_ratings, rating_of
from .tiebreak import BEST_THIRDS_ADVANCING

# Composite-key weights. points dominates, then goal difference, then goals
# scored. The +500 offsets negative goal differences into a positive range.
_PTS_W = 1_000_000.0
_GD_W = 1_000.0
_GD_OFFSET = 500.0


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

    base_pts, base_gf, base_ga = _base_arrays(tournament, teams, idx)

    # Broadcast the played-match base onto every simulation.
    pts = np.tile(base_pts, (n_sims, 1)).astype(np.float64)
    gf = np.tile(base_gf, (n_sims, 1)).astype(np.float64)
    ga = np.tile(base_ga, (n_sims, 1)).astype(np.float64)

    _play_remaining(tournament, idx, pts, gf, ga, rng, home_advantage, ratings, n_sims)

    gd = gf - ga
    # Per-team jitter < 1 breaks exact ties without ever overtaking a real
    # one-goal difference (goal counts are integers, so differ by >= 1).
    jitter = rng.random((n_sims, n_teams)) * 0.5
    key = pts * _PTS_W + (gd + _GD_OFFSET) * _GD_W + gf + jitter

    qualified = np.zeros((n_sims, n_teams), dtype=bool)
    third_keys = np.empty((n_sims, len(tournament.groups)), dtype=np.float64)
    third_team = np.empty((n_sims, len(tournament.groups)), dtype=np.int64)

    for g, (group, members) in enumerate(tournament.groups.items()):
        member_idx = np.array([idx[t] for t in members])
        group_key = key[:, member_idx]                 # (n_sims, 4)
        order = np.argsort(-group_key, axis=1)         # best-first
        # Top two of each group advance automatically.
        for rank in (0, 1):
            winners = member_idx[order[:, rank]]
            qualified[np.arange(n_sims), winners] = True
        # Stash the third-placed team for the cross-group comparison.
        third_local = order[:, 2]
        third_team[:, g] = member_idx[third_local]
        third_keys[:, g] = group_key[np.arange(n_sims), third_local]

    _advance_best_thirds(qualified, third_keys, third_team, n_sims)

    counts = qualified.sum(axis=0)
    probs = {team: float(counts[i]) / n_sims for team, i in idx.items()}
    return SimulationResult(probabilities=probs, n_sims=n_sims)


def _base_arrays(tournament: Tournament, teams: List[str], idx: Dict[str, int]):
    """Points / goals-for / goals-against from *played* matches only."""
    records = build_records(tournament)
    for match in tournament.matches:
        apply_match(records, match)
    n = len(teams)
    pts = np.zeros(n, dtype=np.float64)
    gf = np.zeros(n, dtype=np.float64)
    ga = np.zeros(n, dtype=np.float64)
    for team, i in idx.items():
        r = records[team]
        pts[i], gf[i], ga[i] = r.points, r.gf, r.ga
    return pts, gf, ga


def _play_remaining(tournament, idx, pts, gf, ga, rng, home_advantage, ratings, n_sims):
    """Sample and fold every unplayed fixture into the per-sim arrays."""
    remaining = [m for m in tournament.matches if not m.played]
    if not remaining:
        return
    kwargs = {} if home_advantage is None else {"home_advantage": home_advantage}
    for m in remaining:
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


def _advance_best_thirds(qualified, third_keys, third_team, n_sims):
    """Mark the eight best third-placed teams (by the same key) as advancing."""
    order = np.argsort(-third_keys, axis=1)            # best third-placed first
    best = order[:, :BEST_THIRDS_ADVANCING]
    rows = np.repeat(np.arange(n_sims), BEST_THIRDS_ADVANCING)
    chosen_groups = best.reshape(-1)
    chosen_teams = third_team[rows, chosen_groups]
    qualified[rows, chosen_teams] = True
