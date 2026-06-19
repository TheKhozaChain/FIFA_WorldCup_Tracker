"""Provider selection + the fetch-with-cache orchestration.

`load_tournament` is the single entry point the CLI uses: it resolves the
provider, serves a fresh cache hit unless `--refresh` is given, and falls back
to the bundled offline snapshot if a live provider fails — so the tool always
prints *something* useful.
"""
from __future__ import annotations

from typing import Optional, Tuple

from ..types import Tournament
from . import cache
from .base import DataProvider, ProviderError
from .football_data import FootballDataProvider
from .offline import OfflineProvider
from .thesportsdb import TheSportsDBProvider

_REGISTRY = {
    FootballDataProvider.name: FootballDataProvider,
    TheSportsDBProvider.name: TheSportsDBProvider,
    OfflineProvider.name: OfflineProvider,
}


def available_providers() -> list:
    return list(_REGISTRY)


def make_provider(name: str) -> DataProvider:
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise ProviderError(
            f"unknown provider '{name}'. Choose one of: {', '.join(_REGISTRY)}"
        )


def load_tournament(
    provider_name: str,
    refresh: bool = False,
    ttl: int = cache.DEFAULT_TTL_SECONDS,
) -> Tuple[Tournament, str]:
    """Return (tournament, note) where `note` describes the data's provenance
    for display (cache hit, live fetch, or offline fallback)."""
    is_offline = provider_name == OfflineProvider.name
    if not refresh:
        cached = cache.load(provider_name, ttl=ttl)
        if cached is not None:
            label = _offline_label(cached) if is_offline else f"cache ({provider_name})"
            return cached, label

    provider = make_provider(provider_name)
    try:
        tournament = provider.fetch()
        cache.save(provider_name, tournament)
        if is_offline:
            return tournament, _offline_label(tournament)
        return tournament, f"live fetch ({provider_name})"
    except ProviderError as exc:
        if is_offline:
            raise
        # Fall back to the bundled snapshot so the tool still runs offline.
        fallback = OfflineProvider().fetch()
        return fallback, f"{_offline_label(fallback)} — live fetch failed: {exc}"


def _offline_label(tournament: Tournament) -> str:
    frozen = tournament.fetched_at or "unknown date"
    return f"⚠ frozen offline snapshot ({frozen}) — run live for latest"
