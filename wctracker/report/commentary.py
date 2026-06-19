"""Generate dynamic "Headline movements" commentary from a run.

Rule-based and deterministic — no LLM, no network. It reads the same rows the
table renders and narrates what moved: who is through, the biggest risers and
fallers (with where the damage clusters), the best-third bubble, and anyone
eliminated. Because it is driven by the numbers, it changes automatically as new
results come in.
"""
from __future__ import annotations

from collections import Counter
from typing import List

from . import ELIMINATED, LIVE, QUALIFIED, Row

# Only call out moves at least this large (percentage points).
_MOVE_THRESHOLD = 2.0
_MAX_PER_LIST = 6


def _pct(v) -> str:
    return "—" if v is None else f"{v:.0f}%"


def _signed(v: float) -> str:
    return f"{v:+.1f}"


def _qualified_line(rows: List[Row]) -> List[str]:
    through = sorted((r for r in rows if r.status == QUALIFIED),
                     key=lambda r: (-r.now, -r.points))
    if not through:
        return ["**Through to the knockouts (✓):** none clinched yet."]
    parts = []
    for r in through:
        tag = f"{r.group}, {r.points} pts"
        if r.won_group:
            tag += ", group won"
        parts.append(f"{r.team} ({tag})")
    return [f"**Through to the knockouts (✓):** " + "; ".join(parts) + "."]


def _risers(rows: List[Row]) -> List[str]:
    risers = [r for r in rows if r.delta is not None and r.delta >= _MOVE_THRESHOLD]
    risers.sort(key=lambda r: r.delta, reverse=True)
    if not risers:
        return []
    out = ["", "**Biggest risers**"]
    for r in risers[:_MAX_PER_LIST]:
        out.append(f"- **{r.team} ({_signed(r.delta)})** — Group {r.group}, "
                   f"now {_pct(r.now)} ({r.points} pts).")
    return out


def _fallers(rows: List[Row]) -> List[str]:
    fallers = [r for r in rows if r.delta is not None and r.delta <= -_MOVE_THRESHOLD]
    fallers.sort(key=lambda r: r.delta)
    if not fallers:
        return []
    out = ["", "**Biggest fallers**"]
    for r in fallers[:_MAX_PER_LIST]:
        note = ""
        if r.status == ELIMINATED:
            note = "; now out."
        elif r.position >= 3 and r.remaining > 0 and r.now < 35:
            note = "; needs a result from its remaining game(s)."
        out.append(f"- **{r.team} ({_signed(r.delta)})** — Group {r.group}, "
                   f"now {_pct(r.now)}{note}")
    # Where is the damage concentrated?
    clusters = Counter(r.group for r in fallers[:_MAX_PER_LIST] if r.delta <= -10)
    hot = sorted(g for g, n in clusters.items() if n >= 2)
    if hot:
        groups = " and ".join(hot) if len(hot) <= 2 else ", ".join(hot)
        out.append(f"\nThe damage is concentrated in Group{'s' if len(hot) > 1 else ''} "
                   f"{groups}, where decisive results have resolved the table.")
    return out


def _bubble(rows: List[Row]) -> List[str]:
    bubble = [r for r in rows if r.position == 3 and r.status == LIVE]
    bubble.sort(key=lambda r: (r.delta if r.delta is not None else 0.0), reverse=True)
    if not bubble:
        return []
    named = ", ".join(
        f"{r.team} ({_signed(r.delta)})" if r.delta is not None else r.team
        for r in bubble[:_MAX_PER_LIST]
    )
    return ["", "**Best-third bubble** (currently 3rd, chasing the 8 best-third spots): "
            + named + "."]


def _eliminated(rows: List[Row]) -> List[str]:
    out_teams = [r for r in rows if r.status == ELIMINATED]
    if not out_teams:
        return ["", "**Eliminated (✗):** none yet."]
    named = ", ".join(f"{r.team} ({r.group})" for r in out_teams)
    return ["", f"**Eliminated (✗):** {named}."]


def build(rows: List[Row], *, n_sims: int, played: int, total: int,
         source_note: str) -> str:
    """Return the markdown 'Headline movements' section for these rows."""
    lines = [
        "## Headline movements",
        "",
        f"_{source_note} · {n_sims:,} simulations · {played} of {total} "
        f"matches played._",
        "",
    ]
    lines += _qualified_line(rows)
    lines += _risers(rows)
    lines += _fallers(rows)
    lines += _bubble(rows)
    lines += _eliminated(rows)
    return "\n".join(lines)
