import pytest
from core.player import Player, PlayerAlreadyExistsError, PlayerStore


def test_player_store_rejects_duplicate_id_and_token() -> None:
    """Adding a player with an existing ID or session token must raise PlayerAlreadyExistsError."""

    store = PlayerStore()
    p1 = Player(name="Alice")
    store.add_player(p1)

    # Duplicate ID
    duplicate_id_player = Player(name="Alice_Clone")
    duplicate_id_player.id = p1.id
    with pytest.raises(PlayerAlreadyExistsError):
        store.add_player(duplicate_id_player)

    # Duplicate Session Token
    duplicate_token_player = Player(name="Alice_Imp")
    duplicate_token_player.session_token = p1.session_token
    with pytest.raises(PlayerAlreadyExistsError):
        store.add_player(duplicate_token_player)


def test_remove_player_migrates_admin_when_host_leaves() -> None:
    """When the admin leaves, admin privileges must be transferred to the next active player."""

    admin = Player(name="Admin", is_admin=True)
    player2 = Player(name="Bob", is_admin=False)
    store = PlayerStore([admin, player2])

    removed = store.remove_player(admin.id)
    assert removed == admin
    assert store.get_by_id(admin.id) is None
    assert store.get_by_session_token(admin.session_token) is None

    # Bob should now be promoted to admin
    current_admin = store.get_admin()
    assert current_admin is not None
    assert current_admin.id == player2.id
    assert current_admin.is_admin is True


def test_player_store_all_ready_logic() -> None:
    """all_ready returns False for empty store or partial ready, and True only when all are ready."""

    store = PlayerStore()
    assert store.all_ready() is False

    p1 = Player(name="Alice", is_ready=False)
    p2 = Player(name="Bob", is_ready=True)
    store.add_player(p1)
    store.add_player(p2)
    assert store.all_ready() is False

    p1.is_ready = True
    assert store.all_ready() is True


def test_is_name_taken_case_insensitive() -> None:
    """Display name collision checks must be case-insensitive and ignore leading/trailing whitespace."""

    store = PlayerStore([Player(name="Alice")])

    assert store.is_name_taken("alice") is True
    assert store.is_name_taken("  ALICE  ") is True
    assert store.is_name_taken("Bob") is False
