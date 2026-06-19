"""Command-line entry point: fetch -> simulate -> diff -> render."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from . import __version__
from .baseline import load_baseline
from .model.simulate import simulate
from .model.standings import compute_standings
from .providers import cache
from .providers.factory import available_providers, load_tournament
from .report import Row, build_rows
from .report import markdown as md_report
from .report import table as table_report
from .types import Tournament

DEFAULT_PROVIDER = "football-data"
LATEST_MD = Path(__file__).resolve().parent.parent / "latest.md"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wctracker",
        description="Live WC2026 group-stage advancement probabilities "
                    "(Start → Now → Δ vs a frozen pre-tournament baseline).",
    )
    p.add_argument("--provider", default=os.getenv("WCTRACKER_PROVIDER", DEFAULT_PROVIDER),
                   choices=available_providers(),
                   help="data source (default from $WCTRACKER_PROVIDER or football-data)")
    p.add_argument("--refresh", action="store_true",
                   help="ignore the local cache and force a live re-fetch")
    p.add_argument("--sims", type=int, default=10_000,
                   help="number of Monte Carlo simulations (default 10000)")
    p.add_argument("--seed", type=int, default=None,
                   help="RNG seed for reproducible output")
    p.add_argument("--group", default=None, metavar="X",
                   help="filter to a single group, e.g. --group C")
    p.add_argument("--home-advantage", type=float, default=None,
                   help="override the home-team Elo nudge (default 30)")
    p.add_argument("--no-markdown", action="store_true",
                   help="skip writing latest.md")
    p.add_argument("--version", action="version", version=f"wctracker {__version__}")
    return p


def _positions(tournament: Tournament) -> Dict[str, int]:
    positions: Dict[str, int] = {}
    for ordered in compute_standings(tournament).values():
        for i, rec in enumerate(ordered, start=1):
            positions[rec.team] = i
    return positions


def _filter_group(rows: List[Row], group: str | None) -> List[Row]:
    if not group:
        return rows
    wanted = group.upper()
    selected = [r for r in rows if r.group.upper() == wanted]
    return selected


def run(argv: List[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)

    ttl = -1 if args.refresh else cache.DEFAULT_TTL_SECONDS
    tournament, note = load_tournament(args.provider, refresh=args.refresh, ttl=ttl)

    result = simulate(
        tournament,
        n_sims=args.sims,
        seed=args.seed,
        home_advantage=args.home_advantage,
    )

    rows = build_rows(
        tournament=tournament,
        now_probs=result.probabilities,
        baseline=load_baseline(),
        positions=_positions(tournament),
    )
    rows = _filter_group(rows, args.group)
    if not rows:
        print(f"No teams found for group '{args.group}'.", file=sys.stderr)
        return 2

    scope = f"Group {args.group.upper()}" if args.group else "All 12 groups"
    title = f"WC2026 Advancement Tracker — {scope}"
    caption = (
        f"source: {note} · sims: {args.sims:,} · played: "
        f"{sum(m.played for m in tournament.matches)}/{len(tournament.matches)} "
        f"· top-2 per group + 8 best 3rd-placed advance"
    )

    table_report.render(rows, title=title, note=caption)

    if not args.no_markdown:
        path = md_report.render(rows, title=title, note=caption, out_path=LATEST_MD)
        print(f"\nMarkdown report written to {path}")
    return 0
