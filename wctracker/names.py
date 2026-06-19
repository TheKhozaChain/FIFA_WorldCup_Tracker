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
    "Mexico", "Korea Republic", "Czechia", "South Africa", "Canada",
    "Switzerland", "Bosnia and Herzegovina", "Qatar", "Scotland", "Morocco",
    "Brazil", "Haiti", "United States", "Australia", "Türkiye", "Paraguay",
    "Germany", "Côte d'Ivoire", "Ecuador", "Curaçao", "Sweden", "Japan",
    "Netherlands", "Tunisia", "New Zealand", "IR Iran", "Belgium", "Egypt",
    "Uruguay", "Saudi Arabia", "Spain", "Cabo Verde", "Norway", "France",
    "Senegal", "Iraq", "Argentina", "Austria", "Jordan", "Algeria", "Colombia",
    "Congo DR", "Portugal", "Uzbekistan", "England", "Ghana", "Panama",
    "Croatia",
}

# Known provider variants -> canonical. Keys are matched accent- and
# case-insensitively (see `_key`), so accent/case-only variants of the
# canonical names resolve automatically; list only different *wordings* here.
_ALIASES = {
    "czech republic": "Czechia",
    "south korea": "Korea Republic",
    "republic of korea": "Korea Republic",
    "turkey": "Türkiye",
    "ivory coast": "Côte d'Ivoire",
    "cape verde": "Cabo Verde",
    "usa": "United States",
    "united states of america": "United States",
    "iran": "IR Iran",
    "iran islamic republic of": "IR Iran",
    "bosnia & herzegovina": "Bosnia and Herzegovina",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "dr congo": "Congo DR",
    "democratic republic of the congo": "Congo DR",
    "dr of the congo": "Congo DR",
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
