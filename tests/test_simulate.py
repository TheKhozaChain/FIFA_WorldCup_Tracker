"""Monte Carlo simulation: invariants + a deterministic cross-check that the
vectorised best-thirds logic agrees with the pure-Python tie-break module."""
import string

from wctracker.model.simulate import simulate
from wctracker.model.standings import compute_standings
from wctracker.model.tiebreak import qualified_teams
from wctracker.providers.offline import OfflineProvider
from wctracker.types import Match, Tournament


def _fully_played_tournament() -> Tournament:
    """12 groups with a strict, tie-free hierarchy and third-placed teams whose
    goal differences increase by group index, so the 8 best thirds are exactly
    the thirds of groups 4..11. Every match is played => zero randomness."""
    groups = {}
    matches = []
    for i, letter in enumerate(string.ascii_uppercase[:12]):
        t1, t2, t3, t4 = (f"{letter}1", f"{letter}2", f"{letter}3", f"{letter}4")
        groups[letter] = [t1, t2, t3, t4]
        margin = i + 1  # third-placed team's goals scored / GD grows with i
        matches += [
            Match(letter, t1, t2, 1, 0, played=True),        # t1 > t2
            Match(letter, t3, t4, margin, 0, played=True),   # t3 > t4 by `margin`
            Match(letter, t1, t3, 1, 0, played=True),        # t1 > t3
            Match(letter, t4, t2, 0, 1, played=True),        # t2 > t4
            Match(letter, t4, t1, 0, 1, played=True),        # t1 > t4
            Match(letter, t2, t3, 1, 0, played=True),        # t2 > t3
        ]
    return Tournament(groups=groups, matches=matches)


def test_probabilities_sum_to_thirty_two():
    # Exactly 32 teams advance in every simulation, so the probabilities — the
    # expected number advancing — must sum to 32.
    t = OfflineProvider().fetch()
    res = simulate(t, n_sims=5000, seed=1)
    assert abs(sum(res.probabilities.values()) - 32.0) < 1e-9


def test_seed_is_reproducible():
    t = OfflineProvider().fetch()
    a = simulate(t, n_sims=2000, seed=7).probabilities
    b = simulate(t, n_sims=2000, seed=7).probabilities
    assert a == b


def test_clinched_team_certain_eliminated_team_impossible():
    # In the fully-played fixture there is nothing left to simulate: each
    # group's winner is certain to advance and its bottom team cannot.
    t = _fully_played_tournament()
    p = simulate(t, n_sims=200, seed=3).probabilities
    assert p["A1"] == 1.0        # group winner, 9 pts
    assert p["A4"] == 0.0        # bottom of group, 0 pts, weakest third


def test_vectorised_advancement_matches_pure_tiebreak():
    t = _fully_played_tournament()
    expected = set(qualified_teams(compute_standings(t)))
    # No unplayed matches and no ties => simulation is fully deterministic.
    probs = simulate(t, n_sims=200, seed=99).probabilities
    sim_qualified = {team for team, p in probs.items() if p > 0.5}

    assert len(expected) == 32
    assert sim_qualified == expected
    # spot-check the best-thirds boundary: groups 4..11 thirds in, 0..3 out.
    assert "E3" in sim_qualified and "L3" in sim_qualified
    assert "A3" not in sim_qualified and "D3" not in sim_qualified
