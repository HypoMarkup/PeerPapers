import pytest
from services.assignment import assign_peer_markers


def test_assign_peer_markers_empty() -> None:
    """Empty player list should return empty assignments."""

    assert assign_peer_markers([]) == {}


def test_assign_peer_markers_single_player() -> None:
    """Single player room should assign the player to self-review for solo demo mode."""

    assert assign_peer_markers(["player_1"]) == {"player_1": "player_1"}


def test_assign_peer_markers_two_players() -> None:
    """Two players should mark each other without self-marking."""

    assignments = assign_peer_markers(["p1", "p2"])
    assert assignments == {"p1": "p2", "p2": "p1"}


def test_assign_peer_markers_multiple_players() -> None:
    """Multiple players should form a valid circular assignment with no self-marking."""

    players = [f"p_{i}" for i in range(5)]
    assignments = assign_peer_markers(players, randomize=False)

    # 1. Every player is assigned to mark someone
    assert set(assignments.keys()) == set(players)

    # 2. Every player's work is marked by someone
    assert set(assignments.values()) == set(players)

    # 3. No player marks their own work
    assert all(marker != author for marker, author in assignments.items())


def test_assign_peer_markers_randomized_validity() -> None:
    """Randomized assignments must still satisfy all bijection and no self-marking invariants."""

    players = [f"p_{i}" for i in range(10)]
    assignments = assign_peer_markers(players, randomize=True)

    assert len(assignments) == len(players)
    assert set(assignments.keys()) == set(players)
    assert set(assignments.values()) == set(players)
    assert all(marker != author for marker, author in assignments.items())
