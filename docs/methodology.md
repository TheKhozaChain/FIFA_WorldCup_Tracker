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
advancement (`model/simulate.py`). Goal sampling is vectorised with numpy; the
ranking is then resolved per simulation so the official tie-breakers apply
exactly.

#### Within-group order (the WC2026 tie-breakers)

This is where 2026 differs from previous World Cups, and getting it wrong
changes who is eliminated. The order (`order_group_h2h`) is:

1. **points**
2. **head-to-head** among the teams level on points — points, then goal
   difference, then goals scored *in the matches between those teams only*
3. **overall goal difference**, then **overall goals scored**
4. **FIFA ranking** (approximated by our `ratings.json`)

The critical point: for 2026 **head-to-head is applied *before* overall goal
difference** — the reverse of Qatar 2022. A team level on points with a rival
that beat it head-to-head cannot overtake that rival on goal difference. (Real
example: Haiti, on 0 points, having lost to Scotland, is eliminated even though
it could in principle finish with a better overall goal difference.)

> **Sources:** FIFA World Cup 2026 regulations, Article 13; corroborated by
> [Sofascore](https://www.sofascore.com/news/__trashed-21),
> [JudgeMate](https://www.judgemate.com/en/guides/world-cup-2026-group-stage-tiebreakers-explained),
> and [GamblingCalc](https://gamblingcalc.com/gambling-guides/world-cup-2026-tiebreaker-rules/).
> We apply head-to-head as a single mini-table pass; the rare recursive
> "re-apply after partial separation" case and the fair-play/disciplinary step
> (we don't model cards) are documented simplifications. Teams identical on every
> modelled criterion fall back to FIFA ranking, then name/id — there is no
> "drawing of lots" in 2026.

#### Best third-placed and elimination

The 12 third-placed teams are then compared **across groups** on points → goal
difference → goals scored → FIFA ranking (no head-to-head — they never met), and
the top 8 advance. A team's probability is the fraction of the N simulations in
which it advanced.

**Elimination** is also computed exactly, not just inferred from "0 simulations":
`is_eliminated_from_group` enumerates every win/draw/loss combination of a
group's remaining fixtures and declares a team out only when it can reach **no**
top-three finish under any of them (honouring head-to-head). This removes the
edge case where a vanishingly small true chance could round to zero sims, and
drives the `✗ out` status in the table.

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
- **Name matching.** Probabilities are keyed by team name. The canonical
  spellings follow FIFA usage (e.g. "Czechia", "Türkiye", "Korea Republic",
  "Côte d'Ivoire", "United States", "IR Iran", "Congo DR"). Live providers run
  every name through `wctracker/names.py` (`canonical()`), which folds common
  alternative wordings ("Czech Republic", "Turkey", "South Korea", …) onto those
  canonical names used by `ratings.json`/`baseline.json`. A genuinely
  unrecognised name still falls back to the default rating / shows "—" for
  Start — add it to `_ALIASES` to fix.
- **Monte Carlo noise.** At N = 10,000, percentages carry roughly ±0.5%. Raise
  `--sims` for steadier numbers; use `--seed` for reproducible output.
