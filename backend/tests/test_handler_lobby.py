import asyncio

from core.player import Player
from generated.v1.messages_pb2 import (
    CreateRoom,
    ErrorCode,
    JoinRoom,
    LeaveRoom,
    ServerMessage,
    SetReady,
    UpdateSettings,
)
from generated.v1.models_pb2 import RoomSettings
from handlers.lobby import (
    handle_create_room,
    handle_join_room,
    handle_leave_room,
    handle_set_ready,
    handle_update_settings,
)
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


def create_context(
    rm: RoomManager | None = None,
    cm: ConnectionManager | None = None,
    ws: FakeWebSocket | None = None,
) -> tuple[Context, RoomManager, ConnectionManager, FakeWebSocket]:
    """Creates a test context with in-memory managers and a fake WebSocket."""

    fake_ws = ws or FakeWebSocket()
    room_mgr = rm or RoomManager()
    conn_mgr = cm or ConnectionManager()
    ctx = Context(ws=fake_ws, room_manager=room_mgr, conn_manager=conn_mgr)  # type: ignore[arg-type]
    return ctx, room_mgr, conn_mgr, fake_ws


# ─── handle_create_room ───


def test_handle_create_room_success() -> None:
    """Valid CreateRoom initializes admin player, room, and returns credentials."""

    async def run() -> None:
        ctx, rm, cm, fake_ws = create_context()
        msg = CreateRoom(
            player_name="Alice",
            password="secret_password",
            settings=RoomSettings(exam_duration_mins=20),
        )

        await handle_create_room(ctx, msg)

        assert ctx.is_authenticated is True
        assert ctx.is_admin is True
        assert ctx.player.name == "Alice"
        assert ctx.room.settings.exam_duration_mins == 20
        assert rm.room_count() == 1

        payload_types = [m.WhichOneof("payload") for m in fake_ws.sent_messages]
        assert "auth_success" in payload_types
        assert "room_created" in payload_types
        assert "room_state_update" in payload_types

    asyncio.run(run())


def test_handle_create_room_validation_errors() -> None:
    """CreateRoom rejects empty names, empty passwords, missing settings, or invalid durations."""

    async def run() -> None:
        # 1. Empty player name
        ctx, _, _, ws = create_context()
        await handle_create_room(ctx, CreateRoom(player_name="", password="pw", settings=RoomSettings(exam_duration_mins=15)))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_ARGUMENT

        # 2. Empty password
        ctx, _, _, ws = create_context()
        await handle_create_room(ctx, CreateRoom(player_name="Alice", password="", settings=RoomSettings(exam_duration_mins=15)))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_ARGUMENT

        # 3. Missing settings
        ctx, _, _, ws = create_context()
        await handle_create_room(ctx, CreateRoom(player_name="Alice", password="pw"))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_ARGUMENT

        # 4. Non-positive duration
        ctx, _, _, ws = create_context()
        await handle_create_room(ctx, CreateRoom(player_name="Alice", password="pw", settings=RoomSettings(exam_duration_mins=0)))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_ARGUMENT

    asyncio.run(run())


# ─── handle_join_room ───


def test_handle_join_room_success() -> None:
    """Student joins an active room with correct credentials and receives AuthSuccess."""

    async def run() -> None:
        ctx_admin, rm, cm, _ = create_context()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="mypassword", admin_player=admin)

        ctx_student, _, _, ws_student = create_context(rm=rm, cm=cm)
        msg = JoinRoom(room_code=room.code, password="mypassword", player_name="Bob")

        await handle_join_room(ctx_student, msg)

        assert ctx_student.is_authenticated is True
        assert ctx_student.is_admin is False
        assert ctx_student.player.name == "Bob"
        assert room.players.count() == 2

        assert ws_student.sent_messages[0].WhichOneof("payload") == "auth_success"
        assert ws_student.sent_messages[0].auth_success.player_id == ctx_student.player.id

    asyncio.run(run())


def test_handle_join_room_errors() -> None:
    """JoinRoom returns specific error codes for missing room, wrong password, or taken name."""

    async def run() -> None:
        ctx_admin, rm, cm, _ = create_context()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="mypassword", admin_player=admin)

        # 1. Empty name
        ctx, _, _, ws = create_context(rm=rm, cm=cm)
        await handle_join_room(ctx, JoinRoom(room_code=room.code, password="mypassword", player_name=""))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_ARGUMENT

        # 2. Non-existent room code
        ctx, _, _, ws = create_context(rm=rm, cm=cm)
        await handle_join_room(ctx, JoinRoom(room_code="XXXXXX", password="mypassword", player_name="Bob"))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_ROOM_NOT_FOUND

        # 3. Wrong password
        ctx, _, _, ws = create_context(rm=rm, cm=cm)
        await handle_join_room(ctx, JoinRoom(room_code=room.code, password="wrongpassword", player_name="Bob"))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_PASSWORD

        # 4. Display name collision (case-insensitive)
        ctx, _, _, ws = create_context(rm=rm, cm=cm)
        await handle_join_room(ctx, JoinRoom(room_code=room.code, password="mypassword", player_name="ADMIN"))
        assert ws.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_NAME_TAKEN

    asyncio.run(run())


# ─── handle_leave_room ───


def test_handle_leave_room_member() -> None:
    """A regular member leaving removes them from the room and unbinds their context."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        member = Player(name="Bob", is_admin=False)
        room.players.add_player(member)

        ctx_member, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_member.bind_session(member, room)

        await handle_leave_room(ctx_member, LeaveRoom())

        assert ctx_member.is_authenticated is False
        assert room.players.count() == 1
        assert room.players.get_by_id(member.id) is None

    asyncio.run(run())


def test_handle_leave_room_admin_migration() -> None:
    """When the admin leaves, admin privileges automatically migrate to the next player."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        member = Player(name="Bob", is_admin=False)
        room.players.add_player(member)

        ctx_admin, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        await handle_leave_room(ctx_admin, LeaveRoom())

        assert room.players.count() == 1
        assert member.is_admin is True
        assert room.players.get_admin() == member

    asyncio.run(run())


def test_handle_leave_room_last_player_deletes_room() -> None:
    """When the last remaining player leaves, the room is deleted from RoomManager."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        await handle_leave_room(ctx_admin, LeaveRoom())

        assert rm.room_count() == 0
        assert rm.get_room(room.code) is None

    asyncio.run(run())


# ─── handle_update_settings & handle_set_ready ───


def test_handle_update_settings_and_ready() -> None:
    """Admin updates duration and players toggle ready status in the lobby."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        # 1. Update settings as admin
        await handle_update_settings(ctx_admin, UpdateSettings(settings=RoomSettings(exam_duration_mins=45)))
        assert room.settings.exam_duration_mins == 45

        # 2. Toggle ready status
        await handle_set_ready(ctx_admin, SetReady(is_ready=True))
        assert admin.is_ready is True

        # 3. Non-admin cannot update settings
        member = Player(name="Bob", is_admin=False)
        room.players.add_player(member)
        ctx_member, _, _, ws_member = create_context(rm=rm, cm=cm)
        ctx_member.bind_session(member, room)

        await handle_update_settings(ctx_member, UpdateSettings(settings=RoomSettings(exam_duration_mins=60)))
        assert ws_member.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_NOT_ADMIN
        # Settings remained 45
        assert room.settings.exam_duration_mins == 45

    asyncio.run(run())
