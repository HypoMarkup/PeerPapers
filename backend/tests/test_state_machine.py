import pytest
from core.state_machine import (
    GuardConditionFailedError,
    IllegalStateTransitionError,
    RoomStateMachine,
)
from generated.v1.models_pb2 import RoomState


def test_state_machine_valid_full_lifecycle() -> None:
    """Happy path through all room states from LOBBY to RESULTS."""

    sm = RoomStateMachine()
    assert sm.state == RoomState.ROOM_STATE_LOBBY

    sm.transition_to_exam(all_players_ready=True, exam_uploaded=True, duration_mins=15)
    assert sm.state == RoomState.ROOM_STATE_EXAM

    sm.transition_to_marking()
    assert sm.state == RoomState.ROOM_STATE_MARKING

    sm.transition_to_results(all_marking_done=True)
    assert sm.state == RoomState.ROOM_STATE_RESULTS


def test_transition_to_exam_guard_failures() -> None:
    """Starting exam must fail if players are not ready, no PDF is uploaded, or duration is invalid."""

    sm = RoomStateMachine()

    with pytest.raises(GuardConditionFailedError, match="All players must be ready"):
        sm.transition_to_exam(all_players_ready=False, exam_uploaded=True, duration_mins=15)

    with pytest.raises(GuardConditionFailedError, match="upload an exam PDF"):
        sm.transition_to_exam(all_players_ready=True, exam_uploaded=False, duration_mins=15)

    with pytest.raises(GuardConditionFailedError, match="greater than 0"):
        sm.transition_to_exam(all_players_ready=True, exam_uploaded=True, duration_mins=0)

    # State must still be LOBBY
    assert sm.state == RoomState.ROOM_STATE_LOBBY


def test_transition_to_results_guard_failure() -> None:
    """Transitioning to results must fail if marking is incomplete."""

    sm = RoomStateMachine()
    sm.state = RoomState.ROOM_STATE_MARKING

    with pytest.raises(GuardConditionFailedError, match="complete marking"):
        sm.transition_to_results(all_marking_done=False)

    assert sm.state == RoomState.ROOM_STATE_MARKING


def test_illegal_state_transition() -> None:
    """Skipping phases (e.g. LOBBY -> RESULTS) must raise IllegalStateTransitionError."""

    sm = RoomStateMachine()
    assert not sm.can_transition_to(RoomState.ROOM_STATE_RESULTS)

    with pytest.raises(IllegalStateTransitionError):
        sm.transition_to_results(all_marking_done=True)


def test_force_next_state_admin_override() -> None:
    """Admin force override advances sequentially and raises when already in RESULTS."""

    sm = RoomStateMachine()

    assert sm.force_next_state() == RoomState.ROOM_STATE_EXAM
    assert sm.force_next_state() == RoomState.ROOM_STATE_MARKING
    assert sm.force_next_state() == RoomState.ROOM_STATE_RESULTS

    with pytest.raises(IllegalStateTransitionError):
        sm.force_next_state()


def test_reset_to_lobby_from_any_state() -> None:
    """Resetting to lobby returns state back to LOBBY."""

    sm = RoomStateMachine()
    sm.state = RoomState.ROOM_STATE_RESULTS
    sm.reset_to_lobby()

    assert sm.state == RoomState.ROOM_STATE_LOBBY
