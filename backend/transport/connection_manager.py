import asyncio
from collections.abc import Iterable

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import WebSocketException

from generated.v1.messages_pb2 import ServerMessage
from utils.constants import DEFAULT_SEND_TIMEOUT
from utils.logger import get_logger

logger = get_logger("transport.connection_manager")


class ConnectionManager:
    """Tracks active WebSocket connections for players and orchestrates message delivery."""

    def __init__(self) -> None:
        """Initializes an empty player-to-socket registry."""

        self._connections: dict[str, ServerConnection] = {}

    def register(self, player_id: str, ws: ServerConnection) -> None:
        """Binds a player ID to their active WebSocket connection."""

        self._connections[player_id] = ws
        logger.info(f"Registered connection for player {player_id}.")

    def unregister(self, player_id: str) -> None:
        """Removes a player's active WebSocket connection."""

        if self._connections.pop(player_id, None) is not None:
            logger.info(f"Unregistered connection for player {player_id}.")
        else:
            logger.warning(f"Attempted to unregister non-existent connection for player {player_id}.")

    def get_connection(self, player_id: str) -> ServerConnection | None:
        """Retrieves the active WebSocket connection for a player, if connected."""

        return self._connections.get(player_id)

    def is_player_connected(self, player_id: str) -> bool:
        """Checks whether a player has an active WebSocket connection."""

        return player_id in self._connections

    async def send_to_player(self, player_id: str, message: ServerMessage | bytes) -> bool:
        """Sends a binary Protobuf ServerMessage to a specific player with a timeout."""

        ws = self._connections.get(player_id)
        if ws is None:
            logger.warning(f"Cannot send message: player {player_id} is not connected.")
            return False

        payload = message if isinstance(message, bytes) else message.SerializeToString()

        try:
            await asyncio.wait_for(ws.send(payload), timeout=DEFAULT_SEND_TIMEOUT)
            return True
        except (TimeoutError, WebSocketException, OSError) as e:
            logger.warning(f"Failed to send message to player {player_id}: {e}")
            self.unregister(player_id)
            return False

    async def broadcast_to_players(
        self,
        player_ids: Iterable[str],
        message: ServerMessage,
        exclude_player_id: str | None = None,
    ) -> None:
        """Broadcasts a binary Protobuf ServerMessage to a list of player IDs concurrently."""

        # Filter out the excluded sender and any players who are not currently connected
        target_ids = [pid for pid in player_ids if pid != exclude_player_id and pid in self._connections]
        if not target_ids:
            return

        payload = message.SerializeToString()

        # Reuse send_to_player for each socket concurrently
        _ = await asyncio.gather(
            *(self.send_to_player(pid, payload) for pid in target_ids),
            return_exceptions=True,
        )
