"""The best-third-placed cross-group comparison — where the subtle bugs live."""
from wctracker.model.tiebreak import (
    BEST_THIRDS_ADVANCING,
    best_thirds_advancing,
    is_eliminated_from_group,
    qualified_teams,
    rank_best_thirds,
)
from wctracker.types import TeamRecord


def _rec(name, pts):
    return TeamRecord(name, "C", won=pts // 3, drawn=pts % 3)


def third(name, pts=0, gd=0, gf=0):
    """A TeamRecord with an exact points/GD/GF profile (wins/goals chosen to
    match), standing in for a third-placed team."""
    # encode points as wins+draws; gd/gf via gf and ga
    won, drawn = divmod(pts, 3)
    return TeamRecord(name, "?", won=won, drawn=drawn, gf=gf, ga=gf - gd)


def test_ranked_by_points_first():
    thirds = [third("low", pts=3, gd=9, gf=9), third("high", pts=4, gd=0, gf=1)]
    assert [t.team for t in rank_best_thirds(thirds)] == ["high", "low"]


def test_goal_difference_breaks_points_tie():
    thirds = [third("a", pts=3, gd=1, gf=5), third("b", pts=3, gd=4, gf=5)]
    assert [t.team for t in rank_best_thirds(thirds)] == ["b", "a"]


def test_goals_scored_breaks_gd_tie():
    thirds = [third("a", pts=3, gd=2, gf=4), third("b", pts=3, gd=2, gf=7)]
    assert [t.team for t in rank_best_thirds(thirds)] == ["b", "a"]


def test_exactly_eight_of_twelve_advance():
    # 12 thirds with strictly increasing strength -> the top 8 advance.
    thirds = [third(f"g{i:02d}", pts=3, gd=i, gf=10 + i) for i in range(12)]
    advancing = best_thirds_advancing(thirds)
    assert len(advancing) == BEST_THIRDS_ADVANCING
    advancing_names = {t.team for t in advancing}
    # the four weakest (i = 0..3) must miss out
    assert advancing_names == {f"g{i:02d}" for i in range(4, 12)}


def test_head_to_head_loss_eliminates_team_on_zero_points():
    # The real Group C situation: Haiti (0 pts) lost head-to-head to Scotland,
    # who is guaranteed >= 3 pts. Under 2026 head-to-head-first rules Haiti can
    # never overtake Scotland for third, so Haiti is eliminated.
    records = [_rec("Brazil", 4), _rec("Morocco", 4), _rec("Scotland", 3), _rec("Haiti", 0)]
    played = [("Haiti", "Scotland", 0, 1)]   # Scotland won the head-to-head
    remaining = [("Scotland", "Brazil"), ("Morocco", "Haiti")]

    assert is_eliminated_from_group("Haiti", records, played, remaining) is True
    # Everyone who can still reach third is alive.
    assert is_eliminated_from_group("Scotland", records, played, remaining) is False
    assert is_eliminated_from_group("Brazil", records, played, remaining) is False


def test_two_losses_is_not_automatic_elimination():
    # A 0-point team is NOT out if the decider against the third-placed rival is
    # still to come — it can win that game and leapfrog on head-to-head.
    records = [_rec("Top", 6), _rec("Second", 6), _rec("Rival", 3), _rec("Us", 0)]
    played = []                       # Us-vs-Rival not played yet
    remaining = [("Us", "Rival")]     # win this and Us draws level, winning H2H
    assert is_eliminated_from_group("Us", records, played, remaining) is False


def test_full_qualified_set_top_two_plus_best_thirds():
    # Two groups, each already fully ordered (1st..4th). Build standings dict.
    def grp(letter, names):
        return [TeamRecord(n, letter, won=w) for n, w in names]

    standings = {
        "A": grp("A", [("A1", 3), ("A2", 2), ("A3", 1), ("A4", 0)]),
        "B": grp("B", [("B1", 3), ("B2", 2), ("B3", 1), ("B4", 0)]),
    }
    # Only 2 groups, so both thirds (A3, B3) fit within the 8 best-third slots.
    qualified = set(qualified_teams(standings))
    assert qualified == {"A1", "A2", "B1", "B2", "A3", "B3"}
    assert "A4" not in qualified and "B4" not in qualified
