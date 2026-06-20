"""Standings logic: the foundation everything else stands on."""
from wctracker.model.standings import (
    apply_match,
    build_records,
    compute_standings,
    order_group,
    order_group_h2h,
)
from wctracker.types import Match, TeamRecord, Tournament


def _single_group(matches):
    return Tournament(groups={"A": ["W", "X", "Y", "Z"]}, matches=matches)


def test_win_draw_loss_points_and_goals():
    t = _single_group([
        Match("A", "W", "X", 2, 0, played=True),   # W win
        Match("A", "Y", "Z", 1, 1, played=True),   # draw
    ])
    rec = build_records(t)
    for m in t.matches:
        apply_match(rec, m)

    assert rec["W"].points == 3 and rec["W"].won == 1 and rec["W"].gd == 2
    assert rec["X"].points == 0 and rec["X"].lost == 1 and rec["X"].gd == -2
    assert rec["Y"].points == 1 and rec["Y"].drawn == 1 and rec["Y"].gf == 1
    assert rec["Z"].points == 1 and rec["Z"].drawn == 1


def test_unplayed_match_is_ignored():
    rec = build_records(_single_group([]))
    apply_match(rec, Match("A", "W", "X", played=False))
    assert rec["W"].played == 0 and rec["X"].played == 0


def test_played_match_requires_scoreline():
    import pytest
    with pytest.raises(ValueError):
        Match("A", "W", "X", played=True)


def test_order_by_points_then_gd_then_gf():
    # same points; B has better GD; C and D tie on GD so goals scored decides.
    records = [
        TeamRecord("A", "A", won=2, drawn=0, lost=1, gf=5, ga=4),   # 6 pts, gd +1
        TeamRecord("B", "A", won=2, drawn=0, lost=1, gf=7, ga=3),   # 6 pts, gd +4
        TeamRecord("C", "A", won=2, drawn=0, lost=1, gf=6, ga=5),   # 6 pts, gd +1, gf 6
        TeamRecord("D", "A", won=2, drawn=0, lost=1, gf=4, ga=3),   # 6 pts, gd +1, gf 4
    ]
    ordered = [r.team for r in order_group(records)]
    assert ordered == ["B", "C", "A", "D"]


def test_equal_records_fall_back_to_alphabetical():
    records = [
        TeamRecord("Zeta", "A", won=1, gf=1, ga=0),
        TeamRecord("Alpha", "A", won=1, gf=1, ga=0),
    ]
    assert [r.team for r in order_group(records)] == ["Alpha", "Zeta"]


def test_head_to_head_outranks_goal_difference():
    # WC2026 rule: teams level on points are split by head-to-head BEFORE
    # overall goal difference. B beat A head-to-head, but A has the better
    # overall GD — B must still rank above A.
    records = [
        TeamRecord("A", "X", won=1, lost=1, gf=6, ga=1),   # 3 pts, GD +5
        TeamRecord("B", "X", won=1, lost=1, gf=2, ga=1),   # 3 pts, GD +1
        TeamRecord("C", "X", drawn=1, lost=1, gf=1, ga=3),
        TeamRecord("D", "X", lost=1, drawn=1, gf=1, ga=5),
    ]
    results = [("B", "A", 1, 0)]   # B beat A in their meeting
    ordered = [r.team for r in order_group_h2h(records, results)]
    assert ordered.index("B") < ordered.index("A")


def test_head_to_head_draw_falls_through_to_goal_difference():
    # If the head-to-head was a draw, the level teams are split on overall GD.
    records = [
        TeamRecord("A", "X", won=1, drawn=1, gf=5, ga=1),  # 4 pts, GD +4
        TeamRecord("B", "X", won=1, drawn=1, gf=2, ga=1),  # 4 pts, GD +1
        TeamRecord("C", "X", lost=2, gf=0, ga=5),
        TeamRecord("D", "X", lost=2, gf=1, ga=2),
    ]
    results = [("A", "B", 1, 1)]   # drew head-to-head
    ordered = [r.team for r in order_group_h2h(records, results)]
    assert ordered.index("A") < ordered.index("B")   # decided by GD +4 vs +1


def test_compute_standings_full_group_order():
    t = _single_group([
        Match("A", "W", "X", 3, 0, played=True),
        Match("A", "Y", "Z", 0, 0, played=True),
        Match("A", "W", "Y", 1, 0, played=True),
        Match("A", "Z", "X", 2, 2, played=True),
    ])
    order = [r.team for r in compute_standings(t)["A"]]
    # W: 2 wins (6). Y: draw+loss (1). Z: 2 draws (2). X: draw+loss (1, worse gd).
    assert order[0] == "W"
    assert order[1] == "Z"
