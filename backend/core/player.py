import secrets
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

from generated.v1.models_pb2 import Player as ProtoPlayer
from utils.logger import get_logger

logger = get_logger("core.player")


@dataclass
class Player:
    """Represents a player in a room."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    session_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    is_connected: bool = True
    is_ready: bool = False
    is_admin: bool = False

    def to_proto(self) -> ProtoPlayer:
        """Converts domain Player into a sanitized Protobuf Player object."""

        return ProtoPlayer(
            id=self.id,
            name=self.name,
            is_connected=self.is_connected,
            is_ready=self.is_ready,
            is_admin=self.is_admin,
        )


class PlayerAlreadyExistsError(Exception):
    """Raised when attempting to add a player whose ID or session token already exists."""


class PlayerStore:
    """Manages the collection of players and their sessions within a room."""

    def __init__(self, players: list[Player] | None = None) -> None:
        players = players or []
        self._players: dict[str, Player] = {p.id: p for p in players}
        self._token_to_id: dict[str, str] = {p.session_token: p.id for p in players}

    def __iter__(self) -> Iterator[Player]:
        """Allows direct iteration over players (e.g. `for p in player_store:`)."""

        return iter(self._players.values())

    def add_player(self, player: Player) -> None:
        """Adds a player to the store and indexes their session token."""

        if player.id in self._players:
            logger.error(f"Cannot add player: ID {player.id} already exists in the room.")
            raise PlayerAlreadyExistsError(f"Player with ID '{player.id}' already exists.")

        if player.session_token in self._token_to_id:
            logger.error(f"Cannot add player with ID {player.id}: session token already exists in the room.")
            raise PlayerAlreadyExistsError("Player with this session token already exists.")

        self._players[player.id] = player
        self._token_to_id[player.session_token] = player.id

    def get_by_id(self, player_id: str) -> Player | None:
        """Retrieves a player by their player ID."""

        return self._players.get(player_id)

    def get_by_session_token(self, session_token: str) -> Player | None:
        """Retrieves a player by their secret session token."""

        player_id = self._token_to_id.get(session_token)
        if player_id is None:
            logger.warning(f"Session token lookup failed for token: {session_token[:6]}...")
            return None

        return self._players.get(player_id)

    def get_all(self) -> list[Player]:
        """Returns all players as a list."""

        return list(self._players.values())

    def get_all_ids(self) -> list[str]:
        """Returns a list of all player IDs."""

        return list(self._players.keys())

    def is_name_taken(self, name: str) -> bool:
        """Checks if a display name is already taken in this room (case-insensitive)."""

        target = name.strip().lower()
        return any(p.name.strip().lower() == target for p in self._players.values())

    def remove_player(self, player_id: str) -> Player | None:
        """Removes a player from the store and migrates admin if the host left."""

        player = self._players.pop(player_id, None)
        if player is None:
            logger.warning(f"Attempted to remove non-existent player with ID: {player_id}")
            return None

        _ = self._token_to_id.pop(player.session_token, None)

        # If the host left, automatically promote the next player
        if player.is_admin and self._players:
            next_admin = next(iter(self._players.values()))
            next_admin.is_admin = True
            logger.warning(
                f"Admin {player.name} ({player.id}) left. Migrated admin rights to {next_admin.name} ({next_admin.id})"
            )

        return player

    def count(self) -> int:
        """Returns the total number of players in the store."""

        return len(self._players)

    def all_ready(self) -> bool:
        """Checks if all players in the room are marked as ready."""

        if not self._players:
            return False
        return all(player.is_ready for player in self._players.values())

    def reset_ready_status(self) -> None:
        """Resets the is_ready flag for all players to False."""

        for player in self._players.values():
            player.is_ready = False

    def get_admin(self) -> Player | None:
        """Returns the current admin player, if any."""

        admin = next((player for player in self._players.values() if player.is_admin), None)
        if admin is None and self._players:
            logger.warning(f"No admin player found in non-empty player store ({len(self._players)} players)")
        return admin

    def to_proto_list(self) -> list[ProtoPlayer]:
        """Returns a list of all players converted to Protobuf Player objects."""

        return [player.to_proto() for player in self._players.values()]
