# predictions/ — locked-in forecasts & model scoring

Dated snapshots of model predictions, committed **before** the matches they
forecast. Git history is the referee: the commit timestamp proves when each
prediction was locked in, so no model can be quietly tuned after results land.

Each file pits the repo's **Monte Carlo** model (`wctracker`) against an
independent **heuristic** model on the same data, lists the predictions, and
leaves blank columns to fill in once the real results are known. After the
matches, score each model by **mean absolute error** against the actual
advance/eliminate outcomes (0 or 100) — lowest wins.

| File | Forecasts | Status |
|---|---|---|
| [2026-06-20-pre-md3.md](2026-06-20-pre-md3.md) | Round-of-32 advancement, before Matchday 3 | ⏳ awaiting MD3 results |
