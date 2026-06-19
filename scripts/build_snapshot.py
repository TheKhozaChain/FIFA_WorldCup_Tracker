"""Regenerate the bundled offline snapshot (wctracker/data/snapshot.json).

Deterministic: seeds a Poisson draw from the committed ratings so the snapshot
is reproducible. This is a dev/maintenance script, not part of the package or
the runtime path. Run:  python scripts/build_snapshot.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from wctracker.fixtures import round_robin
from wctracker.model.strength import expected_goals, load_ratings, rating_of

# Illustrative WC2026-style draw: 12 groups (A-L) of 4, seeded by pot.
GROUPS = {
    "A": ["Spain", "Colombia", "Canada", "Cameroon"],
    "B": ["France", "Morocco", "Ukraine", "Algeria"],
    "C": ["Argentina", "Mexico", "Sweden", "Qatar"],
    "D": ["England", "USA", "Nigeria", "Saudi Arabia"],
    "E": ["Brazil", "Switzerland", "Serbia", "Ghana"],
    "F": ["Portugal", "Japan", "Egypt", "Costa Rica"],
    "G": ["Netherlands", "Senegal", "Poland", "Jamaica"],
    "H": ["Germany", "Denmark", "Iran", "Panama"],
    "I": ["Belgium", "Ecuador", "Wales", "Uzbekistan"],
    "J": ["Italy", "Austria", "Ivory Coast", "New Zealand"],
    "K": ["Croatia", "Korea Republic", "Peru", "Jordan"],
    "L": ["Uruguay", "Australia", "Tunisia", "Cape Verde"],
}

# Mark the first four pairings of each group's round-robin as played
# (match-days 1 and 2), leaving the last two fixtures still to come.
PLAYED_PER_GROUP = 4
FETCHED_AT = "2026-06-18T20:00:00Z"
SEED = 2026


def main() -> None:
    rng = np.random.default_rng(SEED)
    ratings = load_ratings()
    results = []
    for group, teams in GROUPS.items():
        for home, away in round_robin(teams)[:PLAYED_PER_GROUP]:
            lam_h, lam_a = expected_goals(rating_of(ratings, home), rating_of(ratings, away))
            hg = int(rng.poisson(lam_h))
            ag = int(rng.poisson(lam_a))
            results.append(
                {"group": group, "home": home, "away": away, "home_goals": hg, "away_goals": ag}
            )

    snapshot = {
        "_comment": (
            "ILLUSTRATIVE sample data, not official FIFA results. Group line-ups "
            "and scores are generated for demo/testing. The live providers "
            "override this entirely. Regenerate with scripts/build_snapshot.py."
        ),
        "fetched_at": FETCHED_AT,
        "groups": GROUPS,
        "results": results,
    }

    out = Path(__file__).resolve().parent.parent / "wctracker" / "data" / "snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"wrote {out} ({len(results)} played matches)")


if __name__ == "__main__":
    main()
