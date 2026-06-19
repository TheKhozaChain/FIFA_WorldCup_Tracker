"""Generate the frozen pre-tournament baseline (data/baseline.json).

The baseline is every team's advancement probability with *zero* matches
played — the reference point the live tool diffs against (Start -> Now -> Delta).
It is committed to the repo and not regenerated on normal runs.

Run:  python scripts/build_baseline.py
"""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from wctracker.model.simulate import simulate
from wctracker.providers.offline import OfflineProvider

# Large N + fixed seed so the committed baseline is stable and low-noise.
N_SIMS = 200_000
SEED = 2026


def main() -> None:
    tournament = OfflineProvider().fetch()
    # Freeze the *pre-tournament* state: same groups, but no match played.
    pre = replace(
        tournament,
        matches=[replace(m, home_goals=None, away_goals=None, played=False)
                 for m in tournament.matches],
    )
    result = simulate(pre, n_sims=N_SIMS, seed=SEED)

    payload = {
        "_comment": "Frozen pre-tournament baseline. Do not regenerate casually.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_sims": N_SIMS,
        "seed": SEED,
        "probabilities": {t: round(p * 100, 2) for t, p in result.probabilities.items()},
    }
    out = Path(__file__).resolve().parent.parent / "data" / "baseline.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"wrote {out} for {len(result.probabilities)} teams (N={N_SIMS})")


if __name__ == "__main__":
    main()
