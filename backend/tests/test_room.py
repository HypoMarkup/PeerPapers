import pytest
from core.player import Player
from core.room import Room, RoomError, RoomPhaseError
from generated.v1.models_pb2 import (
    MarkingResult,
    RoomSettings,
    RoomState,
    SectionFeedback,
    SubmissionSection,
)


def test_room_password_verification() -> None:
    """Room bcrypt password verification correctly validates matching and non-matching passwords."""

    admin = Player(name="Admin", is_admin=True)
    room = Room(code="TEST01", password="secret_password", admin_player=admin)

    assert room.verify_password("secret_password") is True
    assert room.verify_password("wrong_password") is False


def test_room_phase_guards() -> None:
    """Mutating methods must raise RoomPhaseError when called in invalid room phases."""

    admin = Player(name="Admin", is_admin=True)
    room = Room(code="TEST01", password="pw", admin_player=admin)

    # 1. save_progress cannot be called in LOBBY
    section = SubmissionSection(section_index=0, text_data="Hello")
    with pytest.raises(RoomPhaseError):
        room.save_progress(admin.id, section)

    # Transition to EXAM
    admin.is_ready = True
    room.set_exam_pdf("exam.pdf", b"%PDF-1.4...")
    room.start_exam()

    # 2. update_settings and set_exam_pdf cannot be called in EXAM
    with pytest.raises(RoomPhaseError):
        room.update_settings(RoomSettings(exam_duration_mins=30))

    with pytest.raises(RoomPhaseError):
        room.set_exam_pdf("new.pdf", b"%PDF...")

    # 3. submit_marking cannot be called in EXAM
    marking = MarkingResult(marker_id=admin.id, author_id=admin.id)
    with pytest.raises(RoomPhaseError):
        room.submit_marking(admin.id, marking)


def test_submit_marking_requires_valid_assignment() -> None:
    """Submitting marking for an unassigned marker must raise RoomError."""

    admin = Player(name="Admin", is_admin=True)
    room = Room(code="TEST01", password="pw", admin_player=admin)

    # Advance to MARKING phase
    room._state_machine.state = RoomState.ROOM_STATE_MARKING

    marking = MarkingResult(marker_id="unassigned_player", author_id=admin.id)
    with pytest.raises(RoomError, match="no peer review assignment"):
        room.submit_marking("unassigned_player", marking)


def test_room_marking_and_results_flow() -> None:
    """Full marking submission and results calculation flow."""

    admin = Player(name="Admin", is_admin=True)
    student = Player(name="Bob", is_admin=False)
    room = Room(code="TEST01", password="pw", admin_player=admin)
    room.players.add_player(student)

    # Advance to MARKING
    room._state_machine.state = RoomState.ROOM_STATE_MARKING
    room.set_marking_assignments({admin.id: student.id, student.id: admin.id})

    assert room.all_marking_submitted() is False

    # Admin marks Student (Bob)
    room.submit_marking(
        admin.id,
        MarkingResult(
            marker_id=admin.id,
            author_id=student.id,
            sections=[SectionFeedback(score=9.0, max_score=10)],
        ),
    )
    assert room.all_marking_submitted() is False

    # Student marks Admin
    room.submit_marking(
        student.id,
        MarkingResult(
            marker_id=student.id,
            author_id=admin.id,
            sections=[SectionFeedback(score=8.0, max_score=10)],
        ),
    )
    assert room.all_marking_submitted() is True

    # Transition to RESULTS & Calculate
    room.end_marking()
    results = room.calculate_results()
    assert len(results) == 2
    assert results[0].player.name == "Bob"
    assert results[0].total_score == 9.0


def test_reset_to_lobby_clears_transient_data() -> None:
    """Resetting room back to LOBBY clears submissions, assignments, and results."""

    admin = Player(name="Admin", is_admin=True)
    room = Room(code="TEST01", password="pw", admin_player=admin)
    room._state_machine.state = RoomState.ROOM_STATE_RESULTS
    room._submissions[admin.id] = {0: SubmissionSection(section_index=0)}
    room._marking_assignments["a"] = "b"
    room.marking_results["b"] = MarkingResult()

    room.reset_to_lobby()

    assert room.state == RoomState.ROOM_STATE_LOBBY
    assert len(room._submissions) == 0
    assert len(room._marking_assignments) == 0
    assert len(room.marking_results) == 0
