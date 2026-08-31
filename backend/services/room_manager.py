import random
import string

from core.player import Player
from core.room import Room
from generated.v1.models_pb2 import RoomSettings
from utils.logger import get_logger

logger = get_logger("services.room_manager")

CODE_LENGTH = 6
MAX_CODE_RETRIES = 100


class RoomCodeCollisionError(Exception):
    """Raised when a unique room code cannot be generated after max retries."""


class RoomManager:
    """Manages the lifecycle of all active rooms on the server."""

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create_room(
        self,
        password: str,
        admin_player: Player,
        settings: RoomSettings | None = None,
    ) -> Room:
        """Creates a new room with a unique code and returns it."""

        code = self._generate_unique_code()
        room = Room(
            code=code,
            password=password,
            admin_player=admin_player,
            settings=settings,
        )
        self._rooms[code] = room
        logger.info(f"Created room {code} by admin {admin_player.name} ({admin_player.id}).")
        return room

    def get_room(self, code: str) -> Room | None:
        """Retrieves a room by its code (case-insensitive)."""

        return self._rooms.get(code.strip().upper())

    def remove_room(self, code: str) -> Room | None:
        """Removes and returns a room by its code, or None if not found."""

        normalized_code = code.strip().upper()
        room = self._rooms.pop(normalized_code, None)
        if room is not None:
            logger.info(f"Removed room {normalized_code}.")
        else:
            logger.warning(f"Attempted to remove non-existent room {normalized_code}.")
        return room

    def list_rooms(self) -> list[Room]:
        """Returns a list of all active rooms."""

        return list(self._rooms.values())

    def room_count(self) -> int:
        """Returns the number of active rooms."""

        return len(self._rooms)

    def _generate_unique_code(self) -> str:
        """Generates a unique uppercase room code."""

        for _ in range(MAX_CODE_RETRIES):
            code = "".join(random.choices(string.ascii_uppercase, k=CODE_LENGTH))
            if code not in self._rooms:
                return code

        logger.error(f"Failed to generate unique room code after {MAX_CODE_RETRIES} attempts.")
        raise RoomCodeCollisionError("Unable to generate a unique room code. Max retries exceeded.")
