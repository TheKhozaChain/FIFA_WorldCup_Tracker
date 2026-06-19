"""The provider interface every data source implements.

Swapping providers means writing one new subclass of `DataProvider` that
returns a `Tournament`. Nothing else in the codebase changes.
"""
from __future__ import annotations

import abc

from ..types import Tournament


class DataProvider(abc.ABC):
    """Fetches WC2026 groups + fixtures and normalises them to `Tournament`."""

    #: short stable id used in --provider, env, and cache filenames
    name: str = "base"

    @abc.abstractmethod
    def fetch(self) -> Tournament:
        """Return the current tournament state.

        Implementations should raise `ProviderError` (below) on auth/network
        failures so the CLI can fall back or report cleanly.
        """
        raise NotImplementedError


class ProviderError(RuntimeError):
    """Raised when a provider cannot return usable data (auth, network, or a
    response shape it does not understand)."""
