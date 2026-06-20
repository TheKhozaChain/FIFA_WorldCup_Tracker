"""Refresh wctracker/data/snapshot.json from the live provider.

Fetches the current real group-stage state (groups, played results, remaining
fixtures) and writes it as the bundled offline snapshot, so the zero-setup
`--provider offline` mode reflects reality as of the refresh. Needs a working
provider key in .env (football-data by default).

Run:  python scripts/build_snapshot.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from wctracker.providers.factory import make_provider


def _validate(groups, matches) -> None:
    members = {g: set(t) for g, t in groups.items()}
    for m in matches:
        assert {m["home"], m["away"]} <= members[m["group"]], \
            f"{m['home']} v {m['away']} not in group {m['group']}"
    for g in groups:
        pairs = {frozenset((m["home"], m["away"])) for m in matches if m["group"] == g}
        assert len(pairs) == 6, f"group {g} has {len(pairs)} unique pairings, expected 6"


def main() -> None:
    load_dotenv()
    provider = make_provider("football-data")
    t = provider.fetch()

    matches = [
        {
            "group": m.group,
            "home": m.home,
            "away": m.away,
            "home_goals": m.home_goals,
            "away_goals": m.away_goals,
            "played": m.played,
        }
        for m in t.matches
    ]
    groups = {g: list(teams) for g, teams in sorted(t.groups.items())}
    _validate(groups, matches)

    played = sum(1 for m in matches if m["played"])
    snapshot = {
        "_comment": (
            "Real WC2026 group-stage state, fetched from football-data.org and "
            "frozen as the offline snapshot. Re-run scripts/build_snapshot.py to "
            "refresh, or use a live provider for current numbers."
        ),
        "fetched_at": (t.fetched_at or date.today().isoformat())[:10],
        "groups": groups,
        "matches": matches,
    }
    out = Path(__file__).resolve().parent.parent / "wctracker" / "data" / "snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out}: {len(matches)} matches ({played} played, "
          f"{len(matches) - played} remaining), as of {snapshot['fetched_at']}")


if __name__ == "__main__":
    main()
