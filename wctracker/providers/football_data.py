"""football-data.org provider (primary).

Why this one: a single authenticated GET to /competitions/WC/matches returns
every group-stage fixture with its group label and full-time score, so we can
build the whole `Tournament` from one request — friendly to the 10-req/min free
tier. Auth is a single `X-Auth-Token` header.

Docs: https://www.football-data.org/documentation/quickstart
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List

import requests

from ..names import canonical
from ..types import Match, Tournament
from .base import DataProvider, ProviderError

BASE_URL = "https://api.football-data.org/v4"
# Competition code for the FIFA World Cup on football-data.org.
COMPETITION = "WC"
FINISHED_STATUSES = {"FINISHED"}


class FootballDataProvider(DataProvider):
    name = "football-data"

    def __init__(self, api_key: str | None = None, timeout: int = 20) -> None:
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY", "")
        self.timeout = timeout

    def fetch(self) -> Tournament:
        if not self.api_key:
            raise ProviderError(
                "FOOTBALL_DATA_API_KEY is not set. Add it to .env, or run with "
                "--provider offline to use the bundled snapshot."
            )
        url = f"{BASE_URL}/competitions/{COMPETITION}/matches"
        try:
            resp = requests.get(
                url,
                headers={"X-Auth-Token": self.api_key},
                params={"stage": "GROUP_STAGE"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network
            raise ProviderError(f"network error contacting football-data.org: {exc}")

        if resp.status_code == 403:
            raise ProviderError(
                "football-data.org rejected the key (403). The free tier may not "
                "cover this competition, or the key is invalid."
            )
        if resp.status_code == 429:
            raise ProviderError("football-data.org rate limit hit (429); try again shortly.")
        if resp.status_code != 200:
            raise ProviderError(f"football-data.org returned HTTP {resp.status_code}")

        return _parse(resp.json())


def _group_letter(raw: str | None) -> str | None:
    """'GROUP_A' -> 'A'. Returns None for matches with no group."""
    if not raw:
        return None
    return raw.replace("GROUP_", "").strip() or None


def _parse(payload: dict) -> Tournament:
    groups: Dict[str, List[str]] = {}
    matches: List[Match] = []

    for m in payload.get("matches", []):
        group = _group_letter(m.get("group") or m.get("stage"))
        if group is None:
            continue
        home = (m.get("homeTeam") or {}).get("name")
        away = (m.get("awayTeam") or {}).get("name")
        if not home or not away:
            continue
        home, away = canonical(home), canonical(away)

        members = groups.setdefault(group, [])
        for team in (home, away):
            if team not in members:
                members.append(team)

        full_time = (m.get("score") or {}).get("fullTime") or {}
        hg, ag = full_time.get("home"), full_time.get("away")
        played = m.get("status") in FINISHED_STATUSES and hg is not None and ag is not None
        matches.append(
            Match(
                group=group,
                home=home,
                away=away,
                home_goals=hg if played else None,
                away_goals=ag if played else None,
                played=played,
            )
        )

    if not groups:
        raise ProviderError("football-data.org returned no group-stage matches.")

    return Tournament(
        groups={g: groups[g] for g in sorted(groups)},
        matches=matches,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source="football-data",
    )
