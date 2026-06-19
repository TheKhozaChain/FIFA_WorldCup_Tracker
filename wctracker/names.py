"""Canonical team names + alias normalisation.

Different providers spell the same nation differently ("Czechia" vs "Czech
Republic", "Türkiye" vs "Turkey", "Korea Republic" vs "South Korea"). The model
keys everything by name — ratings, baseline, standings — so a mismatch silently
drops a team to the default rating and shows "—" for its baseline. Every
provider runs team names through `canonical()` so they line up with the names
used in `data/ratings.json` and `data/baseline.json`.
"""
from __future__ import annotations

import unicodedata

# The canonical spelling for each of the 48 teams (matches ratings/baseline).
CANONICAL = {
    "Mexico", "South Korea", "Czech Republic", "South Africa", "Canada",
    "Switzerland", "Bosnia and Herzegovina", "Qatar", "Scotland", "Morocco",
    "Brazil", "Haiti", "USA", "Australia", "Turkey", "Paraguay", "Germany",
    "Ivory Coast", "Ecuador", "Curacao", "Sweden", "Japan", "Netherlands",
    "Tunisia", "New Zealand", "Iran", "Belgium", "Egypt", "Uruguay",
    "Saudi Arabia", "Spain", "Cape Verde", "Norway", "France", "Senegal",
    "Iraq", "Argentina", "Austria", "Jordan", "Algeria", "Colombia",
    "DR Congo", "Portugal", "Uzbekistan", "England", "Ghana", "Panama",
    "Croatia",
}

# Known provider variants -> canonical. Keys are matched accent- and
# case-insensitively (see `_key`), so only genuinely different wordings need
# listing here, not every accent/case variation.
_ALIASES = {
    "czechia": "Czech Republic",
    "korea republic": "South Korea",
    "republic of korea": "South Korea",
    "turkiye": "Turkey",
    "cote d'ivoire": "Ivory Coast",
    "cote divoire": "Ivory Coast",
    "ivory coast": "Ivory Coast",
    "cabo verde": "Cape Verde",
    "united states": "USA",
    "united states of america": "USA",
    "ir iran": "Iran",
    "iran islamic republic of": "Iran",
    "bosnia & herzegovina": "Bosnia and Herzegovina",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "bosnia and herzegovina": "Bosnia and Herzegovina",
    "congo dr": "DR Congo",
    "dr congo": "DR Congo",
    "democratic republic of the congo": "DR Congo",
    "dr of the congo": "DR Congo",
}


def _key(name: str) -> str:
    """Accent-stripped, lower-cased, punctuation-light lookup key."""
    stripped = "".join(
        c for c in unicodedata.normalize("NFKD", name)
        if not unicodedata.combining(c)
    )
    cleaned = stripped.lower().replace(".", "").replace("'", "").strip()
    return " ".join(cleaned.split())


# Pre-index canonical names by their own key so e.g. "CURACAO" or "curaçao"
# resolve back to "Curacao" without an explicit alias entry.
_BY_KEY = {_key(n): n for n in CANONICAL}
_BY_KEY.update({_key(k): v for k, v in _ALIASES.items()})


def canonical(name: str) -> str:
    """Return the canonical team name, or the input unchanged if unknown."""
    return _BY_KEY.get(_key(name), name)
