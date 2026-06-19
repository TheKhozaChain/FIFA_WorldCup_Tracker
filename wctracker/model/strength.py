"""Team strength -> expected goals.

The model is deliberately simple and interpretable (see docs/methodology.md):
we turn an Elo-style rating *difference* into an expected goal *difference*,
then split that around a baseline scoring rate to get a Poisson mean (lambda)
for each side. Sampling goals — rather than just win/draw/loss — is what makes
the goal-difference and goals-scored tie-breakers work correctly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

# Average goals a single team scores in a men's international (~1.35).
GOAL_BASE = 1.35
# Elo points that correspond to one goal of expected supremacy.
ELO_PER_GOAL = 250.0
# Nominal home-team nudge. WC venues are largely neutral, so keep this small;
# it is applied to whichever team is listed as `home` in the fixture.
HOME_ADVANTAGE = 30.0
# Floor so a heavy underdog never has a literally-zero scoring rate.
MIN_LAMBDA = 0.15

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_ratings(path: Path | None = None) -> Dict[str, float]:
    """Load the ratings table. Keys starting with `_` are config, not teams."""
    path = path or (_DATA_DIR / "ratings.json")
    raw = json.loads(path.read_text())
    default = float(raw.get("_default", 1500))
    ratings = {k: float(v) for k, v in raw.items() if not k.startswith("_")}
    ratings["__default__"] = default
    return ratings


def rating_of(ratings: Dict[str, float], team: str) -> float:
    return ratings.get(team, ratings.get("__default__", 1500.0))


def expected_goals(
    home_rating: float,
    away_rating: float,
    home_advantage: float = HOME_ADVANTAGE,
) -> Tuple[float, float]:
    """Return (lambda_home, lambda_away): the Poisson means for each side."""
    diff = (home_rating + home_advantage) - away_rating
    supremacy = diff / ELO_PER_GOAL          # expected goal difference
    lam_home = max(MIN_LAMBDA, GOAL_BASE + supremacy / 2.0)
    lam_away = max(MIN_LAMBDA, GOAL_BASE - supremacy / 2.0)
    return lam_home, lam_away
