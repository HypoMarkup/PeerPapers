import asyncio

from core.player import Player
from generated.v1.messages_pb2 import (
    Authenticate,
    ErrorCode,
    ServerMessage,
)
from handlers.connection import handle_authenticate, handle_disconnect
from services.room_manager import RoomManager
from transport.connection_manager import ConnectionManager
from transport.context import Context


class FakeWebSocket:
    """Fake WebSocket connection recording sent binary payloads for testing."""

    def __init__(self) -> None:
        self.sent_messages: list[ServerMessage] = []

    async def send(self, data: bytes) -> None:
        msg = ServerMessage.FromString(data)
        self.sent_messages.append(msg)


def create_context(ws: FakeWebSocket | None = None) -> tuple[Context, RoomManager, ConnectionManager, FakeWebSocket]:
    """Creates a test context with in-memory managers and a fake WebSocket."""

    fake_ws = ws or FakeWebSocket()
    rm = RoomManager()
    cm = ConnectionManager()
    ctx = Context(ws=fake_ws, room_manager=rm, conn_manager=cm)  # type: ignore[arg-type]
    return ctx, rm, cm, fake_ws


def test_handle_authenticate_success() -> None:
    """Valid session token binds the returning player and broadcasts reconnect snapshot."""

    async def run() -> None:
        ctx, rm, cm, fake_ws = create_context()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="secret", admin_player=admin)

        # Disconnect the admin initially
        admin.is_connected = False

        msg = Authenticate(session_token=admin.session_token)
        await handle_authenticate(ctx, msg)

        assert ctx.is_authenticated is True
        assert ctx.player == admin
        assert ctx.room == room
        assert admin.is_connected is True

        # Should have sent AuthSuccess to client
        assert len(fake_ws.sent_messages) >= 1
        assert fake_ws.sent_messages[0].WhichOneof("payload") == "auth_success"
        assert fake_ws.sent_messages[0].auth_success.player_id == admin.id

    asyncio.run(run())


def test_handle_authenticate_invalid_token() -> None:
    """Invalid session token responds with an unauthorized error message."""

    async def run() -> None:
        ctx, rm, cm, fake_ws = create_context()
        admin = Player(name="Admin", is_admin=True)
        _ = rm.create_room(password="secret", admin_player=admin)

        msg = Authenticate(session_token="non_existent_token")
        await handle_authenticate(ctx, msg)

        assert ctx.is_authenticated is False
        assert len(fake_ws.sent_messages) == 1
        assert fake_ws.sent_messages[0].WhichOneof("payload") == "error"
        assert fake_ws.sent_messages[0].error.code == ErrorCode.ERROR_CODE_UNAUTHORIZED

    asyncio.run(run())


def test_handle_disconnect_authenticated() -> None:
    """Disconnecting an authenticated player sets is_connected to False and unbinds socket."""

    async def run() -> None:
        ctx, rm, cm, fake_ws = create_context()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="secret", admin_player=admin)
        ctx.bind_session(admin, room)

        assert admin.is_connected is True
        assert cm.is_player_connected(admin.id) is True

        await handle_disconnect(ctx)

        assert admin.is_connected is False
        assert ctx.player is None
        assert ctx.room is None
        assert cm.is_player_connected(admin.id) is False
        # Player must remain in the room store for reconnection
        assert room.players.get_by_id(admin.id) is not None

    asyncio.run(run())


def test_handle_disconnect_unauthenticated() -> None:
    """Disconnecting an unauthenticated socket completes without error."""

    async def run() -> None:
        ctx, rm, cm, fake_ws = create_context()
        await handle_disconnect(ctx)

        assert ctx.player is None
        assert ctx.room is None

    asyncio.run(run())
