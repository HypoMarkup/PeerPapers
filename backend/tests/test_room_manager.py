from unittest.mock import patch
import pytest
from core.player import Player
from services.room_manager import RoomCodeCollisionError, RoomManager


def test_room_manager_create_and_get_case_insensitive() -> None:
    """Creating a room and retrieving it by code is case-insensitive."""

    manager = RoomManager()
    admin = Player(name="Admin", is_admin=True)

    room = manager.create_room(password="secret", admin_player=admin)

    assert len(room.code) == 6
    assert manager.room_count() == 1

    # Exact, lowercase, and padded lookups
    assert manager.get_room(room.code) == room
    assert manager.get_room(room.code.lower()) == room
    assert manager.get_room(f"  {room.code.lower()}  ") == room
    assert manager.get_room("NONEXISTENT") is None


def test_room_manager_remove_room() -> None:
    """Removing a room removes it from the registry, while non-existent codes return None."""

    manager = RoomManager()
    admin = Player(name="Admin", is_admin=True)
    room = manager.create_room(password="secret", admin_player=admin)

    removed = manager.remove_room(room.code.lower())
    assert removed == room
    assert manager.room_count() == 0
    assert manager.get_room(room.code) is None

    # Removing again returns None
    assert manager.remove_room("UNKNOWN") is None


def test_generate_unique_code_collision_exhaustion() -> None:
    """Exhausting retry attempts during code collision must raise RoomCodeCollisionError."""

    manager = RoomManager()

    # Mock random.choices to always return the same colliding code 'COLLID'
    with patch("random.choices", return_value=list("COLLID")):
        manager._rooms["COLLID"] = None  # Force collision

        with pytest.raises(RoomCodeCollisionError):
            manager._generate_unique_code()
