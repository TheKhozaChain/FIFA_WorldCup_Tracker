"""Status classification, group-winner clinch, and commentary generation."""
from wctracker.report import (
    ELIMINATED,
    LIVE,
    QUALIFIED,
    Row,
    _group_winners,
    status_of,
)
from wctracker.report import commentary
from wctracker.types import TeamRecord


def test_status_of_thresholds():
    assert status_of(1.0) == QUALIFIED
    assert status_of(0.0) == ELIMINATED
    assert status_of(0.5) == LIVE


def test_group_winner_clinched_on_points():
    standings = {
        "A": [
            TeamRecord("Leader", "A", won=2, drawn=1),   # 7 pts
            TeamRecord("Chaser", "A", won=1),            # 3 pts, max 3+3=6 < 7
            TeamRecord("Third", "A", drawn=1),
            TeamRecord("Last", "A"),
        ]
    }
    remaining = {"Leader": 0, "Chaser": 1, "Third": 1, "Last": 1}
    assert _group_winners(standings, remaining) == {"Leader"}


def test_group_winner_not_clinched_when_catchable():
    standings = {
        "A": [
            TeamRecord("Leader", "A", won=1),            # 3 pts
            TeamRecord("Chaser", "A", won=1),            # 3 pts, max 3+3=6 > 3
            TeamRecord("Third", "A"),
            TeamRecord("Last", "A"),
        ]
    }
    remaining = {"Leader": 1, "Chaser": 1, "Third": 1, "Last": 1}
    assert _group_winners(standings, remaining) == set()


def _rows():
    return [
        Row("Mexico", "A", start=85.0, now=100.0, position=1, points=6,
            won_group=True, status=QUALIFIED),
        Row("Czechia", "A", start=67.0, now=30.0, position=3, points=1,
            remaining=1, status=LIVE),
        Row("Cabo Verde", "H", start=24.0, now=43.0, position=3, points=1,
            remaining=2, status=LIVE),
        Row("Haiti", "C", start=14.0, now=0.0, position=4, status=ELIMINATED),
    ]


def test_commentary_has_all_sections():
    md = commentary.build(_rows(), n_sims=10000, played=28, total=72,
                          source_note="live")
    assert "## Headline movements" in md
    assert "Mexico" in md and "group won" in md         # through line
    assert "Biggest risers" in md
    assert "Biggest fallers" in md and "Czechia" in md
    assert "Best-third bubble" in md and "Cabo Verde" in md
    assert "Eliminated (✗)" in md and "Haiti" in md


def test_commentary_reports_no_eliminations_cleanly():
    rows = [r for r in _rows() if r.status != ELIMINATED]
    md = commentary.build(rows, n_sims=1000, played=10, total=72, source_note="x")
    assert "Eliminated (✗):** none yet." in md
