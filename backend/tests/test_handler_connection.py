import asyncio

from core.player import Player
from generated.v1.messages_pb2 import (
    Authenticate,
    ErrorCode,
    ForceEndPhase,
    ServerMessage,
    StartExam,
    UploadExam,
)
from generated.v1.models_pb2 import SubmissionSection
from handlers.connection import handle_authenticate, handle_disconnect
from handlers.exam import (
    handle_force_end_exam,
    handle_save_progress,
    handle_start_exam,
)
from handlers.lobby import handle_upload_exam
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


def test_handle_authenticate_during_exam_phase_delivers_progress() -> None:
    """Reconnecting during the EXAM phase delivers the player's saved progress."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        alice = Player(name="Alice", is_admin=True, is_ready=True)
        room = rm.create_room(password="pw", admin_player=alice)

        ctx_alice, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_alice.bind_session(alice, room)

        await handle_upload_exam(ctx_alice, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_alice, StartExam())

        from generated.v1.messages_pb2 import SaveProgress

        await handle_save_progress(
            ctx_alice,
            SaveProgress(
                section=SubmissionSection(
                    section_index=0,
                    text_data="Alice answer",
                    whiteboard_data='{"elements":[]}',
                )
            ),
        )

        # Disconnect Alice
        await handle_disconnect(ctx_alice)
        assert alice.is_connected is False

        # Alice reconnects with a fresh socket
        ctx_reconnect, _, _, ws_reconnect = create_context(rm=rm, cm=cm)
        await handle_authenticate(ctx_reconnect, Authenticate(session_token=alice.session_token))

        assert ctx_reconnect.is_authenticated is True
        assert alice.is_connected is True

        payload_types = [m.WhichOneof("payload") for m in ws_reconnect.sent_messages]
        assert "auth_success" in payload_types
        assert "return_progress" in payload_types

        return_msg = next(m for m in ws_reconnect.sent_messages if m.WhichOneof("payload") == "return_progress")
        assert len(return_msg.return_progress.submission.sections) == 1
        assert return_msg.return_progress.submission.sections[0].text_data == "Alice answer"
        assert return_msg.return_progress.submission.sections[0].whiteboard_data == '{"elements":[]}'

    asyncio.run(run())


def test_handle_authenticate_during_marking_phase_delivers_assignment() -> None:
    """Reconnecting during the MARKING phase delivers the player's assigned paper."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        alice = Player(name="Alice", is_admin=True, is_ready=True)
        bob = Player(name="Bob", is_admin=False, is_ready=True)
        room = rm.create_room(password="pw", admin_player=alice)
        room.players.add_player(bob)

        ctx_alice, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_alice.bind_session(alice, room)

        ctx_bob, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_bob.bind_session(bob, room)

        await handle_upload_exam(ctx_alice, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_alice, StartExam())

        from generated.v1.messages_pb2 import SaveProgress

        await handle_save_progress(ctx_alice, SaveProgress(section=SubmissionSection(section_index=0, text_data="Alice work")))
        await handle_save_progress(ctx_bob, SaveProgress(section=SubmissionSection(section_index=0, text_data="Bob work")))

        # Disconnect Bob
        await handle_disconnect(ctx_bob)
        assert bob.is_connected is False

        # Host transitions to MARKING while Bob is offline
        await handle_force_end_exam(ctx_alice, ForceEndPhase())

        # Bob reconnects with a fresh socket
        ctx_bob_reconnect, _, _, ws_bob_reconnect = create_context(rm=rm, cm=cm)
        await handle_authenticate(ctx_bob_reconnect, Authenticate(session_token=bob.session_token))

        assert ctx_bob_reconnect.is_authenticated is True
        assert bob.is_connected is True

        # Bob must have received both AuthSuccess and MarkingAssignment
        payload_types = [m.WhichOneof("payload") for m in ws_bob_reconnect.sent_messages]
        assert "auth_success" in payload_types
        assert "marking_assignment" in payload_types

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
