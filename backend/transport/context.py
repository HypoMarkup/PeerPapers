import asyncio

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import WebSocketException

from core.player import Player
from core.room import Room
from generated.v1.messages_pb2 import ErrorCode, ErrorMessage, RoomStateUpdate, ServerMessage
from services.room_manager import RoomManager
from transport.connection_manager import ConnectionManager
from utils.constants import DEFAULT_SEND_TIMEOUT
from utils.logger import get_logger

logger = get_logger("transport.context")


class Context:
    """Represents a client's active session state and provides messaging helper methods."""

    def __init__(
        self,
        ws: ServerConnection,
        room_manager: RoomManager,
        conn_manager: ConnectionManager,
    ) -> None:
        self.ws: ServerConnection = ws
        self.room_manager: RoomManager = room_manager
        self.conn_manager: ConnectionManager = conn_manager
        self.player: Player | None = None
        self.room: Room | None = None

    @property
    def is_authenticated(self) -> bool:
        """Returns True if this connection is bound to an active Player and Room."""

        return self.player is not None and self.room is not None

    @property
    def is_admin(self) -> bool:
        """Returns True if the authenticated player has admin privileges in their room."""

        return self.player is not None and self.player.is_admin

    def bind_session(self, player: Player, room: Room) -> None:
        """Binds this WebSocket connection to an active Player and Room session."""

        self.player = player
        self.room = room
        self.conn_manager.register(player.id, self.ws)

    def unbind_session(self) -> None:
        """Clears the active Player and Room bindings from this connection context."""

        if self.player is not None:
            self.conn_manager.unregister(self.player.id)

        self.player = None
        self.room = None

    async def send(self, message: ServerMessage) -> None:
        """Sends a binary Protobuf ServerMessage directly to this connection."""

        try:
            await asyncio.wait_for(self.ws.send(message.SerializeToString()), timeout=DEFAULT_SEND_TIMEOUT)
        except (TimeoutError, WebSocketException, OSError) as e:
            logger.warning(f"Failed to send message: {e}")
            if self.player is not None:
                self.conn_manager.unregister(self.player.id)

    async def send_error(self, code: ErrorCode, message: str) -> None:
        """Constructs and sends a structured ErrorMessage proto to this connection."""

        error_proto = ServerMessage(error=ErrorMessage(code=code, message=message))
        await self.send(error_proto)

    async def broadcast_to_room(
        self,
        message: ServerMessage,
        exclude_self: bool = False,
    ) -> None:
        """Broadcasts a binary Protobuf ServerMessage to all connected players in the current room."""

        if self.room is None:
            logger.warning("Cannot broadcast message to room: context has no bound room.")
            return

        exclude_id = self.player.id if (exclude_self and self.player is not None) else None
        await self.conn_manager.broadcast_to_players(
            player_ids=self.room.players.get_all_ids(),
            message=message,
            exclude_player_id=exclude_id,
        )

    async def broadcast_room_snapshot(self, exclude_self: bool = False) -> None:
        """Broadcasts the latest RoomSnapshot to all connected players in the current room."""

        if self.room is None:
            logger.warning("Cannot broadcast snapshot: context has no bound room.")
            return

        snapshot_message = ServerMessage(room_state_update=RoomStateUpdate(room=self.room.to_snapshot()))
        await self.broadcast_to_room(snapshot_message, exclude_self=exclude_self)
