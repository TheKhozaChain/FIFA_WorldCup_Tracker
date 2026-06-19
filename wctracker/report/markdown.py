"""Write the report to a shareable markdown file (latest.md): the generated
commentary followed by the full table."""
from __future__ import annotations

from pathlib import Path
from typing import List

from . import ELIMINATED, QUALIFIED, Row

_STATUS_TEXT = {QUALIFIED: "✓ Qualified", ELIMINATED: "✗ Out"}


def _fmt_status(status: str) -> str:
    return _STATUS_TEXT.get(status, "· Live")


def _fmt_pct(value) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _fmt_delta(value) -> str:
    if value is None:
        return "—"
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "•")
    return f"{arrow} {value:+.1f}"


def render(rows: List[Row], title: str, note: str, out_path: Path,
          commentary: str = "") -> Path:
    lines = [f"# {title}", "", f"_{note}_", ""]
    if commentary:
        lines += [commentary, "", "---", ""]
    lines += [
        "| Team | Group | Status | Start % | Now % | Δ |",
        "| --- | :---: | :---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r.team} | {r.group} | {_fmt_status(r.status)} | "
            f"{_fmt_pct(r.start)} | {_fmt_pct(r.now)} | {_fmt_delta(r.delta)} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines))
    return out_path
