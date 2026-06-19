# Probability methodology

This note explains exactly how `wctracker` turns match results into the
advancement percentages it prints. None of it is a black box.

## What "advancement" means

WC2026 has **48 teams in 12 groups of 4 (A–L)**. From each group:

- the **top 2** advance automatically, and
- the **8 best third-placed teams** across all 12 groups also advance,

for **32 teams** in the Round of 32. "Probability" here is each team's chance of
being in that 32, given the results so far and a model of the games still to
come. (This is group-stage *advancement* in the finals — not the regional
qualifiers that decided the 48-team field.)

## The pipeline

```
results ─▶ current standings ─▶ Monte Carlo over remaining fixtures ─▶ P(advance)
                                          │
              frozen baseline.json ───────┴──▶ Start → Now → Δ
```

### 1. Current standings

Played matches are folded into points (3/1/0), goals for, and goals against
(`model/standings.py`). This part is pure and deterministic.

### 2. Match outcome model (why we simulate *scorelines*)

Tie-breakers depend on **goal difference** and **goals scored**, so simulating
only win/draw/loss is not enough — we need actual goals. Each team has an
Elo-style **rating** (`wctracker/data/ratings.json`). For a fixture we convert
the rating difference into an expected goal difference and split it around a
baseline scoring rate to get a Poisson mean (λ) for each side
(`model/strength.py`):

```
diff       = (home_rating + home_advantage) − away_rating
supremacy  = diff / ELO_PER_GOAL                 # expected goal difference
λ_home     = max(MIN, GOAL_BASE + supremacy / 2)
λ_away     = max(MIN, GOAL_BASE − supremacy / 2)
```

Defaults: `GOAL_BASE = 1.35`, `ELO_PER_GOAL = 250`, `HOME_ADVANTAGE = 30`
(small — WC venues are largely neutral), `MIN_LAMBDA = 0.15`. Goals are then
drawn as independent `Poisson(λ_home)` and `Poisson(λ_away)`.

### 3. Monte Carlo simulation

For `N` simulations (default 10,000, `--sims`), for **every unplayed fixture**
we sample a scoreline and add it onto the current standings, then resolve
advancement (`model/simulate.py`). The whole thing is **vectorised over N** with
numpy, so 10,000 runs take a fraction of a second.

Ranking uses a single composite key that encodes the FIFA order exactly:

```
key = points·10⁶ + (goal_difference + 500)·10³ + goals_scored + jitter
```

- **points** dominate, then **goal difference**, then **goals scored** — the
  same order as the pure-Python `model/tiebreak.py`.
- `jitter` is a per-team random value in `[0, 0.5)`. It only ever decides teams
  that are otherwise *exactly* tied (goal counts are integers, so a real
  one-goal edge is ≥ 1 and never overturned). This stands in for the
  competition's final "drawing of lots".

Within each group the top 2 by key advance. The 12 third-placed teams are then
compared **by the same key across groups**, and the top 8 advance. A team's
probability is the fraction of the N simulations in which it advanced.

> **Tie-break scope.** FIFA's full group rules add head-to-head and fair-play
> steps before lots. For the *cross-group* best-third comparison there is no
> head-to-head (the teams never met), so points → GD → goals scored → lots is
> the correct and complete order. Within a group we apply points → GD → goals
> scored and resolve any remaining exact tie randomly, omitting the head-to-head
> sub-step — a documented simplification that affects only teams level on all
> three primary criteria.

### 4. Baseline and Δ

`data/baseline.json` is the **frozen pre-tournament** run: the same model with
**zero** matches played, at high N for low noise (see
`scripts/build_baseline.py`). Every live run reports **Start** (baseline),
**Now** (current simulation), and **Δ = Now − Start**, sorted by Δ. It is
committed so the diff is stable and shared by everyone who clones the repo.

## Assumptions & limitations

- **Independent Poisson** ignores in-game correlation (e.g. a team chasing a
  result). Adequate for tournament-level probabilities; not a betting model.
- **Static ratings.** Ratings are pre-tournament seeds and are *not* updated by
  in-tournament form. Swap in your own `ratings.json` to change priors.
- **Name matching.** Probabilities are keyed by team name. If a live provider
  spells a team differently from `ratings.json`/`baseline.json`, that team falls
  back to the default rating / shows "—" for Start. Align the names to fix.
- **Monte Carlo noise.** At N = 10,000, percentages carry roughly ±0.5%. Raise
  `--sims` for steadier numbers; use `--seed` for reproducible output.
