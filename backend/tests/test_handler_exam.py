import asyncio

from core.player import Player
from generated.v1.messages_pb2 import (
    ErrorCode,
    ForceEndPhase,
    RequestExamPdf,
    SaveProgress,
    ServerMessage,
    StartExam,
    UploadExam,
)
from generated.v1.models_pb2 import RoomState, SubmissionSection
from handlers.exam import (
    handle_force_end_exam,
    handle_request_exam_pdf,
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


# ─── handle_start_exam ───


def test_handle_start_exam_success() -> None:
    """Admin starts the exam when all players are ready and PDF is uploaded."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True, is_ready=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        # Upload exam PDF first
        await handle_upload_exam(ctx_admin, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))

        # Start exam
        await handle_start_exam(ctx_admin, StartExam())

        assert room.state == RoomState.ROOM_STATE_EXAM
        latest_msg = ws_admin.sent_messages[-1]
        assert latest_msg.WhichOneof("payload") == "room_state_update"
        assert latest_msg.room_state_update.room.state == RoomState.ROOM_STATE_EXAM

    asyncio.run(run())


def test_handle_start_exam_guards() -> None:
    """StartExam rejects non-admins, not ready players, or missing PDF."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True, is_ready=False)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        # 1. Players not ready
        await handle_start_exam(ctx_admin, StartExam())
        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_PLAYERS_NOT_READY

        # Mark ready, but no PDF uploaded
        admin.is_ready = True
        await handle_start_exam(ctx_admin, StartExam())
        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_EXAM_NOT_UPLOADED

        # Upload PDF, but non-admin attempts to start
        await handle_upload_exam(ctx_admin, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))

        member = Player(name="Bob", is_admin=False, is_ready=True)
        room.players.add_player(member)
        ctx_member, _, _, ws_member = create_context(rm=rm, cm=cm)
        ctx_member.bind_session(member, room)

        await handle_start_exam(ctx_member, StartExam())
        assert ws_member.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_NOT_ADMIN

    asyncio.run(run())


# ─── handle_save_progress ───


def test_handle_save_progress_success() -> None:
    """Student autosaves section text and whiteboard during EXAM phase."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True, is_ready=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        await handle_upload_exam(ctx_admin, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_admin, StartExam())

        # Save progress for Section 0
        section = SubmissionSection(
            section_index=0,
            text_data="My typed essay answer",
            whiteboard_data='{"paths": [{"x": 10, "y": 20}]}',
        )
        await handle_save_progress(ctx_admin, SaveProgress(section=section))

        submission = room.get_submission(admin.id)
        assert submission is not None
        assert len(submission.sections) == 1
        assert submission.sections[0].text_data == "My typed essay answer"
        assert submission.sections[0].whiteboard_data == '{"paths": [{"x": 10, "y": 20}]}'

    asyncio.run(run())


def test_handle_save_progress_wrong_phase() -> None:
    """Saving progress in LOBBY phase is rejected with INVALID_PHASE."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        section = SubmissionSection(section_index=0, text_data="test")
        await handle_save_progress(ctx_admin, SaveProgress(section=section))

        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_STATE

    asyncio.run(run())


# ─── handle_request_exam_pdf ───


def test_handle_request_exam_pdf_success() -> None:
    """Student requests exam PDF and receives ExamPdfContent."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True, is_ready=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, _ = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        pdf_payload = b"%PDF-1.4 Mock exam binary content"
        await handle_upload_exam(ctx_admin, UploadExam(filename="calc_exam.pdf", file_data=pdf_payload))

        # Add member and request the PDF
        member = Player(name="Bob", is_admin=False)
        room.players.add_player(member)
        ctx_member, _, _, ws_member = create_context(rm=rm, cm=cm)
        ctx_member.bind_session(member, room)

        await handle_request_exam_pdf(ctx_member, RequestExamPdf())

        latest_msg = ws_member.sent_messages[-1]
        assert latest_msg.WhichOneof("payload") == "exam_pdf_content"
        assert latest_msg.exam_pdf_content.filename == "calc_exam.pdf"
        assert latest_msg.exam_pdf_content.file_data == pdf_payload

    asyncio.run(run())


def test_handle_request_exam_pdf_not_uploaded() -> None:
    """Requesting exam PDF when none was uploaded returns EXAM_NOT_UPLOADED error."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()
        admin = Player(name="Admin", is_admin=True)
        room = rm.create_room(password="pw", admin_player=admin)

        ctx_admin, _, _, ws_admin = create_context(rm=rm, cm=cm)
        ctx_admin.bind_session(admin, room)

        # No PDF uploaded yet
        await handle_request_exam_pdf(ctx_admin, RequestExamPdf())

        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_EXAM_NOT_UPLOADED

    asyncio.run(run())


# ─── handle_force_end_exam ───


def test_handle_force_end_exam_success() -> None:
    """Admin ending exam transitions to MARKING, generates peer assignments, and delivers papers."""

    async def run() -> None:
        rm = RoomManager()
        cm = ConnectionManager()

        alice = Player(name="Alice", is_admin=True, is_ready=True)
        bob = Player(name="Bob", is_admin=False, is_ready=True)
        room = rm.create_room(password="pw", admin_player=alice)
        room.players.add_player(bob)

        ctx_alice, _, _, ws_alice = create_context(rm=rm, cm=cm)
        ctx_alice.bind_session(alice, room)

        ctx_bob, _, _, ws_bob = create_context(rm=rm, cm=cm)
        ctx_bob.bind_session(bob, room)

        await handle_upload_exam(ctx_alice, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_alice, StartExam())

        # Admin ends the exam
        await handle_force_end_exam(ctx_alice, ForceEndPhase())
        assert room.state == RoomState.ROOM_STATE_MARKING

        # Both Alice and Bob must have received private MarkingAssignment messages
        alice_payloads = [m.WhichOneof("payload") for m in ws_alice.sent_messages]
        bob_payloads = [m.WhichOneof("payload") for m in ws_bob.sent_messages]
        assert "marking_assignment" in alice_payloads
        assert "marking_assignment" in bob_payloads

    asyncio.run(run())


def test_handle_force_end_exam_guards() -> None:
    """Non-admin or calling outside EXAM phase is rejected."""

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

        # 1. Cannot end exam while still in LOBBY phase
        await handle_force_end_exam(ctx_admin, ForceEndPhase())
        assert ws_admin.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_INVALID_STATE

        # Start exam
        await handle_upload_exam(ctx_admin, UploadExam(filename="exam.pdf", file_data=b"%PDF..."))
        await handle_start_exam(ctx_admin, StartExam())

        # 2. Non-admin cannot end exam
        await handle_force_end_exam(ctx_member, ForceEndPhase())
        assert ws_member.sent_messages[-1].error.code == ErrorCode.ERROR_CODE_NOT_ADMIN

    asyncio.run(run())
