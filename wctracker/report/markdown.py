"""Write the same report to a shareable markdown file (latest.md)."""
from __future__ import annotations

from pathlib import Path
from typing import List

from . import Row


def _fmt_pct(value) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _fmt_delta(value) -> str:
    if value is None:
        return "—"
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "•")
    return f"{arrow} {value:+.1f}"


def render(rows: List[Row], title: str, note: str, out_path: Path) -> Path:
    lines = [
        f"# {title}",
        "",
        f"_{note}_",
        "",
        "| Team | Group | Start % | Now % | Δ |",
        "| --- | :---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r.team} | {r.group} | {_fmt_pct(r.start)} | "
            f"{_fmt_pct(r.now)} | {_fmt_delta(r.delta)} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines))
    return out_path
