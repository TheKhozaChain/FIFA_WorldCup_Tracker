"""Build wctracker/data/snapshot.json from real WC2026 group-stage results.

Curated from the official/Wikipedia group pages as of 2026-06-19. Each group
lists its played results (with scorelines) and its remaining fixtures, in real
home/away orientation. Re-run after new match-days to refresh the offline
snapshot:  python scripts/build_snapshot.py

This is a maintenance script, not part of the runtime path. For always-current
numbers use a live provider instead of the frozen snapshot.
"""
from __future__ import annotations

import json
from pathlib import Path

FETCHED_AT = "2026-06-19"

GROUPS = {
    "A": ["Mexico", "Korea Republic", "Czechia", "South Africa"],
    "B": ["Canada", "Switzerland", "Bosnia and Herzegovina", "Qatar"],
    "C": ["Scotland", "Morocco", "Brazil", "Haiti"],
    "D": ["United States", "Australia", "Türkiye", "Paraguay"],
    "E": ["Germany", "Côte d'Ivoire", "Ecuador", "Curaçao"],
    "F": ["Sweden", "Japan", "Netherlands", "Tunisia"],
    "G": ["New Zealand", "IR Iran", "Belgium", "Egypt"],
    "H": ["Uruguay", "Saudi Arabia", "Spain", "Cabo Verde"],
    "I": ["Norway", "France", "Senegal", "Iraq"],
    "J": ["Argentina", "Austria", "Jordan", "Algeria"],
    "K": ["Colombia", "Congo DR", "Portugal", "Uzbekistan"],
    "L": ["England", "Ghana", "Panama", "Croatia"],
}

# (group, home, away, home_goals, away_goals) for matches already played.
PLAYED = [
    ("A", "Mexico", "South Africa", 2, 0),
    ("A", "Korea Republic", "Czechia", 2, 1),
    ("A", "Czechia", "South Africa", 1, 1),
    ("A", "Mexico", "Korea Republic", 1, 0),

    ("B", "Canada", "Bosnia and Herzegovina", 1, 1),
    ("B", "Qatar", "Switzerland", 1, 1),
    ("B", "Switzerland", "Bosnia and Herzegovina", 4, 1),
    ("B", "Canada", "Qatar", 6, 0),

    ("C", "Brazil", "Morocco", 1, 1),
    ("C", "Haiti", "Scotland", 0, 1),

    ("D", "United States", "Paraguay", 4, 1),
    ("D", "Australia", "Türkiye", 2, 0),

    ("E", "Germany", "Curaçao", 7, 1),
    ("E", "Côte d'Ivoire", "Ecuador", 1, 0),

    ("F", "Netherlands", "Japan", 2, 2),
    ("F", "Sweden", "Tunisia", 5, 1),

    ("G", "Belgium", "Egypt", 1, 1),
    ("G", "IR Iran", "New Zealand", 2, 2),

    ("H", "Spain", "Cabo Verde", 0, 0),
    ("H", "Saudi Arabia", "Uruguay", 1, 1),

    ("I", "France", "Senegal", 3, 1),
    ("I", "Iraq", "Norway", 1, 4),

    ("J", "Argentina", "Algeria", 3, 0),
    ("J", "Austria", "Jordan", 3, 1),

    ("K", "Portugal", "Congo DR", 1, 1),
    ("K", "Uzbekistan", "Colombia", 1, 3),

    ("L", "England", "Croatia", 4, 2),
    ("L", "Ghana", "Panama", 1, 0),
]

# (group, home, away) for fixtures not yet played, in real schedule orientation.
REMAINING = [
    ("A", "Czechia", "Mexico"), ("A", "South Africa", "Korea Republic"),

    ("B", "Switzerland", "Canada"), ("B", "Bosnia and Herzegovina", "Qatar"),

    ("C", "Scotland", "Morocco"), ("C", "Brazil", "Haiti"),
    ("C", "Scotland", "Brazil"), ("C", "Morocco", "Haiti"),

    ("D", "United States", "Australia"), ("D", "Türkiye", "Paraguay"),
    ("D", "Türkiye", "United States"), ("D", "Paraguay", "Australia"),

    ("E", "Germany", "Côte d'Ivoire"), ("E", "Ecuador", "Curaçao"),
    ("E", "Curaçao", "Côte d'Ivoire"), ("E", "Ecuador", "Germany"),

    ("F", "Netherlands", "Sweden"), ("F", "Tunisia", "Japan"),
    ("F", "Japan", "Sweden"), ("F", "Tunisia", "Netherlands"),

    ("G", "Belgium", "IR Iran"), ("G", "New Zealand", "Egypt"),
    ("G", "Egypt", "IR Iran"), ("G", "New Zealand", "Belgium"),

    ("H", "Spain", "Saudi Arabia"), ("H", "Uruguay", "Cabo Verde"),
    ("H", "Cabo Verde", "Saudi Arabia"), ("H", "Uruguay", "Spain"),

    ("I", "France", "Iraq"), ("I", "Norway", "Senegal"),
    ("I", "Norway", "France"), ("I", "Senegal", "Iraq"),

    ("J", "Argentina", "Austria"), ("J", "Jordan", "Algeria"),
    ("J", "Algeria", "Austria"), ("J", "Jordan", "Argentina"),

    ("K", "Portugal", "Uzbekistan"), ("K", "Colombia", "Congo DR"),
    ("K", "Colombia", "Portugal"), ("K", "Congo DR", "Uzbekistan"),

    ("L", "England", "Ghana"), ("L", "Panama", "Croatia"),
    ("L", "Panama", "England"), ("L", "Croatia", "Ghana"),
]


def _validate() -> None:
    members = {g: set(t) for g, t in GROUPS.items()}
    for g, h, a, *_ in PLAYED:
        assert {h, a} <= members[g], f"played {h} v {a} not in group {g}"
    for g, h, a in REMAINING:
        assert {h, a} <= members[g], f"remaining {h} v {a} not in group {g}"
    # every group must end up with all 6 unique pairings exactly once
    for g, teams in GROUPS.items():
        pairs = {frozenset((h, a)) for gg, h, a, *_ in PLAYED if gg == g}
        pairs |= {frozenset((h, a)) for gg, h, a in REMAINING if gg == g}
        assert len(pairs) == 6, f"group {g} has {len(pairs)} unique pairings, expected 6"


def main() -> None:
    _validate()
    matches = []
    for g, h, a, hg, ag in PLAYED:
        matches.append({"group": g, "home": h, "away": a,
                        "home_goals": hg, "away_goals": ag, "played": True})
    for g, h, a in REMAINING:
        matches.append({"group": g, "home": h, "away": a,
                        "home_goals": None, "away_goals": None, "played": False})

    snapshot = {
        "_comment": (
            "Real WC2026 group-stage state as of 2026-06-19, curated from the "
            "official/Wikipedia group pages. Frozen snapshot — re-run "
            "scripts/build_snapshot.py to refresh, or use a live provider for "
            "current numbers."
        ),
        "fetched_at": FETCHED_AT,
        "groups": GROUPS,
        "matches": matches,
    }
    out = Path(__file__).resolve().parent.parent / "wctracker" / "data" / "snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    played = sum(1 for m in matches if m["played"])
    print(f"wrote {out}: {len(matches)} matches ({played} played, "
          f"{len(matches) - played} remaining)")


if __name__ == "__main__":
    main()
