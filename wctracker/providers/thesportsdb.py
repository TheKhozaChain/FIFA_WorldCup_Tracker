"""TheSportsDB provider (zero-setup alternative).

Included mainly to demonstrate the provider interface is genuinely swappable:
a second real API, different JSON shape, same `Tournament` out. TheSportsDB's
free test key is the literal string "3". Coverage of live group standings is
less reliable than football-data.org, so this is a fallback, not the default.

Docs: https://www.thesportsdb.com/api.php
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List

import requests

from ..types import Match, Tournament
from .base import DataProvider, ProviderError

BASE_URL = "https://www.thesportsdb.com/api/v1/json"


class TheSportsDBProvider(DataProvider):
    name = "thesportsdb"

    def __init__(self, api_key: str | None = None, league_id: str | None = None,
                 timeout: int = 20) -> None:
        # "3" is TheSportsDB's documented free test key.
        self.api_key = api_key or os.getenv("THESPORTSDB_KEY", "3")
        # League id for the World Cup event season must be configured by the
        # user once the season exists; left overridable via env.
        self.league_id = league_id or os.getenv("THESPORTSDB_LEAGUE_ID", "")
        self.timeout = timeout

    def fetch(self) -> Tournament:  # pragma: no cover - network/coverage varies
        if not self.league_id:
            raise ProviderError(
                "THESPORTSDB_LEAGUE_ID is not set. TheSportsDB needs the WC "
                "season league id; use --provider football-data or offline instead."
            )
        url = f"{BASE_URL}/{self.api_key}/eventsseason.php"
        try:
            resp = requests.get(
                url, params={"id": self.league_id, "s": "2026"}, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ProviderError(f"network error contacting TheSportsDB: {exc}")
        if resp.status_code != 200:
            raise ProviderError(f"TheSportsDB returned HTTP {resp.status_code}")
        return _parse(resp.json())


def _parse(payload: dict) -> Tournament:  # pragma: no cover
    groups: Dict[str, List[str]] = {}
    matches: List[Match] = []
    for e in payload.get("events") or []:
        group = (e.get("strGroup") or "").replace("Group ", "").strip()
        home, away = e.get("strHomeTeam"), e.get("strAwayTeam")
        if not group or not home or not away:
            continue
        members = groups.setdefault(group, [])
        for team in (home, away):
            if team not in members:
                members.append(team)
        hg, ag = e.get("intHomeScore"), e.get("intAwayScore")
        played = hg not in (None, "") and ag not in (None, "")
        matches.append(
            Match(
                group=group, home=home, away=away,
                home_goals=int(hg) if played else None,
                away_goals=int(ag) if played else None,
                played=played,
            )
        )
    if not groups:
        raise ProviderError("TheSportsDB returned no usable group events.")
    return Tournament(
        groups={g: groups[g] for g in sorted(groups)},
        matches=matches,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source="thesportsdb",
    )
