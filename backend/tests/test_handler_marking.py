import asyncio

from core.player import Player
from generated.v1.messages_pb2 import (
    ErrorCode,
    ForceEndPhase,
    SaveProgress,
    ServerMessage,
    StartExam,
    SubmitMarking,
    UploadExam,
)
from generated.v1.models_pb2 import (
    MarkingResult,
    RoomState,
    SectionFeedback,
    SubmissionSection,
)
from handlers.exam import (
    handle_force_end_exam,
    handle_save_progress,
    handle_start_exam,
)
from handlers.lobby import handle_upload_exam
from handlers.marking import (
    handle_force_end_marking,
    handle_submit_marking,
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


# ─── handle_submit_marking ───


def test_handle_submit_marking_auto_advances_to_results() -> None:
    """Submitting marks advances the room to RESULTS when all markers finish."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        # Create 2 players: Alice (Admin) and Bob
        alice = Player(name="Alice", is_admin=True, is_ready=True)
        bob = Player(name="Bob", is_admin=False, is_ready=True)
        room = rm.create_room(password="pw", admin_player=alice)
        room.players.add_player(bob)

        ctx_alice, _, _, ws_alice = create_context(rm=rm, cm=cm)
        ctx_alice.bind_session(alice, room)

        ctx_bob, _, _, ws_bob = create_context(rm=rm, cm=cm)
        ctx_bob.bind_session(bob, room)

        # Upload and start exam
        await handle_upload_exam(ctx_alice, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_alice, StartExam())

        # Save answers
        await handle_save_progress(ctx_alice, SaveProgress(section=SubmissionSection(section_index=0, text_data="Alice answer")))
        await handle_save_progress(ctx_bob, SaveProgress(section=SubmissionSection(section_index=0, text_data="Bob answer")))

        # End exam -> MARKING
        await handle_force_end_exam(ctx_alice, ForceEndPhase())
        assert room.state == RoomState.ROOM_STATE_MARKING

        # 1. Alice marks Bob's paper
        alice_marking = MarkingResult(
            sections=[SectionFeedback(section_index=0, score=90, max_score=100)]
        )
        await handle_submit_marking(ctx_alice, SubmitMarking(result=alice_marking))

        # Not all marking completed yet -> still in MARKING
        assert room.state == RoomState.ROOM_STATE_MARKING

        # 2. Bob marks Alice's paper
        bob_marking = MarkingResult(
            sections=[SectionFeedback(section_index=0, score=85, max_score=100)]
        )
        await handle_submit_marking(ctx_bob, SubmitMarking(result=bob_marking))

        # All marking complete -> automatically transitioned to RESULTS!
        assert room.state == RoomState.ROOM_STATE_RESULTS

        # Verify results broadcast was sent
        payload_types = [m.WhichOneof("payload") for m in ws_alice.sent_messages]
        assert "results_broadcast" in payload_types

        # Alice scored 85 (marked by Bob), Bob scored 90 (marked by Alice)
        results_msg = next(m for m in ws_alice.sent_messages if m.WhichOneof("payload") == "results_broadcast")
        results = results_msg.results_broadcast.results
        assert len(results) == 2
        # Bob is #1 (90), Alice is #2 (85)
        assert results[0].player.name == "Bob"
        assert results[0].total_score == 90
        assert results[1].player.name == "Alice"
        assert results[1].total_score == 85

    asyncio.run(run())


def test_handle_submit_marking_wrong_phase() -> None:
    """Submitting marking outside the MARKING phase is rejected with INVALID_STATE."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        # Room is in LOBBY phase
        marking = MarkingResult(sections=[SectionFeedback(section_index=0, score=50, max_score=100)])
        await handle_submit_marking(ctx_admin, SubmitMarking(result=marking))

        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_STATE

    asyncio.run(run())


# ─── handle_force_end_marking ───


def test_handle_force_end_marking_success() -> None:
    """Admin forcing MARKING -> RESULTS calculates leaderboard and broadcasts results."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        alice = Player(name="Alice", is_admin=True, is_ready=True)
        bob = Player(name="Bob", is_admin=False, is_ready=True)
        room = rm.create_room(password="pw", admin_player=alice)
        room.players.add_player(bob)

        ctx_alice, _, _, ws_alice = create_context(rm=rm, cm=cm)
        ctx_alice.bind_session(alice, room)

        ctx_bob, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_bob.bind_session(bob, room)

        await handle_upload_exam(ctx_alice, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_alice, StartExam())
        await handle_force_end_exam(ctx_alice, ForceEndPhase())
        assert room.state == RoomState.ROOM_STATE_MARKING

        # Only Alice submits marking
        alice_marking = MarkingResult(
            sections=[SectionFeedback(section_index=0, score=95, max_score=100)]
        )
        await handle_submit_marking(ctx_alice, SubmitMarking(result=alice_marking))

        # Admin forces MARKING -> RESULTS early
        await handle_force_end_marking(ctx_alice, ForceEndPhase())
        assert room.state == RoomState.ROOM_STATE_RESULTS

        payload_types = [m.WhichOneof("payload") for m in ws_alice.sent_messages]
        assert "results_broadcast" in payload_types

    asyncio.run(run())


def test_handle_force_end_marking_guards() -> None:
    """Non-admin or calling outside MARKING phase is rejected."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        admin = Player(name="Admin", is_admin=True, is_ready=True)
        member = Player(name="Bob", is_admin=False, is_ready=True)
        room = rm.create_room(password="pw", admin_player=admin)
        room.players.add_player(member)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        ctx_member, _, _, ws_member = create_context(rm=rm, cm=cm)
        ctx_member.bind_session(member, room)

        # 1. Cannot end marking while in LOBBY phase
        await handle_force_end_marking(ctx_admin, ForceEndPhase())
        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_STATE

        # Transition to MARKING
        await handle_upload_exam(ctx_admin, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_admin, StartExam())
        await handle_force_end_exam(ctx_admin, ForceEndPhase())
        assert room.state == RoomState.ROOM_STATE_MARKING

        # 2. Non-admin cannot end marking
        await handle_force_end_marking(ctx_member, ForceEndPhase())
        assert ws_member.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_NOT_ADMIN

    asyncio.run(run())
