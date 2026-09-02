from generated.v1.models_pb2 import RoomState


class StateMachineError(Exception):
    """Base exception for state machine errors."""


class IllegalStateTransitionError(StateMachineError):
    """Raised when an invalid state transition is attempted."""


class GuardConditionFailedError(StateMachineError):
    """Raised when transition guards (e.g. not all players ready) are not met."""


class PlayersNotReadyError(GuardConditionFailedError):
    """Raised when not all players are marked ready before exam start."""


class ExamNotUploadedError(GuardConditionFailedError):
    """Raised when an exam PDF has not been uploaded before exam start."""


class RoomStateMachine:
    """Manages state transitions for a Room."""

    def __init__(self):
        self.state: RoomState = RoomState.ROOM_STATE_LOBBY

    def can_transition_to(self, target_state: RoomState) -> bool:
        """Checks whether transitioning to the target state is structurally valid."""

        valid_transitions = {
            (RoomState.ROOM_STATE_LOBBY, RoomState.ROOM_STATE_EXAM),
            (RoomState.ROOM_STATE_EXAM, RoomState.ROOM_STATE_MARKING),
            (RoomState.ROOM_STATE_MARKING, RoomState.ROOM_STATE_EXAM),
            (RoomState.ROOM_STATE_MARKING, RoomState.ROOM_STATE_RESULTS),
        }

        return (self.state, target_state) in valid_transitions

    def transition_to_exam(
        self,
        all_players_ready: bool,
        exam_uploaded: bool,
        duration_mins: int,
    ) -> None:
        """Transition from LOBBY -> EXAM with guard validation."""

        if not self.can_transition_to(RoomState.ROOM_STATE_EXAM):
            raise IllegalStateTransitionError(f"Cannot transition from {self.state} to {RoomState.ROOM_STATE_EXAM}.")
        if not all_players_ready:
            raise PlayersNotReadyError("All players must be ready before the exam can start.")
        if not exam_uploaded:
            raise ExamNotUploadedError("You must upload an exam PDF before the exam can start.")
        if duration_mins <= 0:
            raise GuardConditionFailedError("Exam duration must be greater than 0 minutes.")

        self.state = RoomState.ROOM_STATE_EXAM

    def transition_to_marking(self) -> None:
        """Transition from EXAM -> MARKING when time expires or forced by admin."""

        if not self.can_transition_to(RoomState.ROOM_STATE_MARKING):
            raise IllegalStateTransitionError(f"Cannot transition from {self.state} to {RoomState.ROOM_STATE_MARKING}.")

        self.state = RoomState.ROOM_STATE_MARKING

    def transition_to_results(self, all_marking_done: bool) -> None:
        """Transition from MARKING -> RESULTS when all markers finished."""

        if not self.can_transition_to(RoomState.ROOM_STATE_RESULTS):
            raise IllegalStateTransitionError(f"Cannot transition from {self.state} to {RoomState.ROOM_STATE_RESULTS}.")
        if not all_marking_done:
            raise GuardConditionFailedError("All players must complete marking before viewing results.")

        self.state = RoomState.ROOM_STATE_RESULTS

    def force_next_state(self) -> RoomState:
        """Admin override: force transition to the immediate next state."""

        next_states = {
            RoomState.ROOM_STATE_LOBBY: RoomState.ROOM_STATE_EXAM,
            RoomState.ROOM_STATE_EXAM: RoomState.ROOM_STATE_MARKING,
            RoomState.ROOM_STATE_MARKING: RoomState.ROOM_STATE_RESULTS,
        }
        if self.state not in next_states:
            raise IllegalStateTransitionError(f"Cannot force next state from {self.state}.")

        self.state = next_states[self.state]
        return self.state

    def reset_to_lobby(self) -> None:
        """Reset the room back to LOBBY state for a new round."""

        self.state = RoomState.ROOM_STATE_LOBBY
