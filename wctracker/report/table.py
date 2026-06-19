"""Render the rows as a clean coloured terminal table via rich."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from . import ELIMINATED, QUALIFIED, Row

# status -> (symbol, rich style)
_STATUS = {
    QUALIFIED: ("✓ in", "bold green"),
    ELIMINATED: ("✗ out", "red"),
}


def _fmt_status(status: str) -> str:
    symbol, style = _STATUS.get(status, ("· live", "dim"))
    return f"[{style}]{symbol}[/]"


def _fmt_pct(value) -> str:
    return "—" if value is None else f"{value:5.1f}%"


def _fmt_delta(value) -> str:
    if value is None:
        return "—"
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "•")
    return f"{arrow} {value:+5.1f}"


def _delta_style(value) -> str:
    if value is None or abs(value) < 0.05:
        return "dim"
    return "green" if value > 0 else "red"


def render(rows: List[Row], title: str, note: str = "") -> None:
    console = Console()
    table = Table(title=title, title_style="bold", caption=note, caption_style="dim")
    table.add_column("Team", style="bold")
    table.add_column("Grp", justify="center")
    table.add_column("Pos", justify="center", style="dim")
    table.add_column("Status", justify="left")
    table.add_column("Start", justify="right")
    table.add_column("Now", justify="right")
    table.add_column("Δ", justify="right")

    for r in rows:
        table.add_row(
            r.team,
            r.group,
            str(r.position) if r.position else "—",
            _fmt_status(r.status),
            _fmt_pct(r.start),
            _fmt_pct(r.now),
            f"[{_delta_style(r.delta)}]{_fmt_delta(r.delta)}[/]",
        )
    console.print(table)
