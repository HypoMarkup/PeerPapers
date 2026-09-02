import time

import bcrypt

from core.player import Player, PlayerStore
from core.state_machine import RoomStateMachine
from generated.v1.models_pb2 import (
    MarkingResult,
    PlayerResult,
    RoomSettings,
    RoomSnapshot,
    RoomState,
    Submission,
    SubmissionSection,
)
from services.scoring import calculate_all_results
from utils.constants import DEFAULT_EXAM_DURATION_MINS
from utils.logger import get_logger

logger = get_logger("core.room")


class RoomError(Exception):
    """Base exception for room-related errors."""


class RoomStateError(RoomError):
    """Raised when an operation is invalid for the current room state."""


class Room:
    """Represents an active exam room and orchestrates its lifecycle and domain state."""

    def __init__(
        self,
        code: str,
        password: str,
        admin_player: Player,
        settings: RoomSettings | None = None,
    ) -> None:
        self.settings: RoomSettings = settings or RoomSettings(exam_duration_mins=DEFAULT_EXAM_DURATION_MINS)
        self.players: PlayerStore = PlayerStore([admin_player])
        self.marking_results: dict[str, MarkingResult] = {}
        self._code: str = code
        self._password_hash: bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self._state_machine: RoomStateMachine = RoomStateMachine()
        self._exam_filename: str | None = None
        self._exam_file_bytes: bytes | None = None
        self._submissions: dict[str, dict[int, SubmissionSection]] = {}
        self._marking_assignments: dict[str, str] = {}
        self._phase_end_time: int = 0

    @property
    def code(self) -> str:
        """Returns the 4-letter room code."""

        return self._code

    @property
    def state(self) -> RoomState:
        """Returns the current RoomState."""

        return self._state_machine.state

    def verify_password(self, password: str) -> bool:
        """Verifies a plain text password against the stored bcrypt hash."""

        return bcrypt.checkpw(password.encode(), self._password_hash)

    def update_settings(self, settings: RoomSettings) -> None:
        """Updates room settings (only allowed in LOBBY state)."""

        if self.state != RoomState.ROOM_STATE_LOBBY:
            logger.warning(f"Cannot update settings in room {self._code}: room is in {self.state}")
            raise RoomStateError("Room settings can only be updated during the LOBBY phase.")

        self.settings = settings

    def set_exam_pdf(self, filename: str, file_bytes: bytes) -> None:
        """Stores the uploaded exam PDF bytes and filename (only allowed in LOBBY state)."""

        if self.state != RoomState.ROOM_STATE_LOBBY:
            logger.warning(f"Cannot upload exam in room {self._code}: room is in {self.state}")
            raise RoomStateError("Exam PDF can only be uploaded during the LOBBY phase.")

        self._exam_filename = filename
        self._exam_file_bytes = file_bytes

    def get_exam_pdf(self) -> tuple[str, bytes] | None:
        """Returns a tuple of (filename, file_bytes) if an exam PDF is uploaded."""

        if self._exam_filename is not None and self._exam_file_bytes is not None:
            return (self._exam_filename, self._exam_file_bytes)
        return None

    def save_progress(self, player_id: str, section: SubmissionSection) -> None:
        """Saves incremental progress for a player section during the EXAM state."""

        if self.state != RoomState.ROOM_STATE_EXAM:
            logger.warning(f"Cannot save progress in room {self._code}: room is in {self.state}")
            raise RoomStateError("Progress can only be saved during the EXAM phase.")

        if player_id not in self._submissions:
            self._submissions[player_id] = {}

        self._submissions[player_id][section.section_index] = section

    def get_submission(self, player_id: str) -> Submission | None:
        """Retrieves a player's complete submission."""

        sections = self._submissions.get(player_id)
        if not sections:
            return None

        return Submission(
            player_id=player_id,
            sections=sorted(sections.values(), key=lambda s: s.section_index),
        )

    def set_marking_assignments(self, assignments: dict[str, str]) -> None:
        """Sets the marker_id -> author_id mapping for peer review."""

        self._marking_assignments = assignments

    def get_assigned_author_id(self, marker_id: str) -> str | None:
        """Returns the author ID assigned to a specific marker."""

        return self._marking_assignments.get(marker_id)

    def submit_marking(self, marker_id: str, result: MarkingResult) -> None:
        """Stores marking feedback submitted by a peer reviewer."""

        if self.state != RoomState.ROOM_STATE_MARKING:
            logger.warning(f"Cannot submit marking in room {self._code}: room is in {self.state}")
            raise RoomStateError("Marking can only be submitted during the MARKING phase.")

        author_id = self._marking_assignments.get(marker_id)
        if author_id is None:
            logger.warning(f"Marker {marker_id} has no assignment in room {self._code}")
            raise RoomError(f"Marker '{marker_id}' has no peer review assignment.")

        self.marking_results[author_id] = result

    def all_marking_submitted(self) -> bool:
        """Checks if all assigned markers have submitted their feedback."""

        if not self._marking_assignments:
            return False

        return set(self._marking_assignments.values()) == set(self.marking_results.keys())

    def start_exam(self) -> None:
        """Transitions the room from LOBBY -> EXAM and computes the end timestamp."""

        self._state_machine.transition_to_exam(
            all_players_ready=self.players.all_ready(),
            exam_uploaded=self._exam_file_bytes is not None,
            duration_mins=self.settings.exam_duration_mins,
        )
        self._phase_end_time = int(time.time() * 1000) + (self.settings.exam_duration_mins * 60 * 1000)
        self.players.reset_ready_status()

    def end_exam(self) -> None:
        """Transitions the room from EXAM -> MARKING and clears phase end time."""

        self._state_machine.transition_to_marking()
        self._phase_end_time = 0

    def end_marking(self) -> None:
        """Transitions the room from MARKING -> RESULTS."""

        self._state_machine.transition_to_results(
            all_marking_done=self.all_marking_submitted(),
        )
        self._phase_end_time = 0

    def force_next_phase(self) -> RoomState:
        """Forces the room into the immediate next phase regardless of guards (admin override)."""

        new_state = self._state_machine.force_next_state()
        self._phase_end_time = 0
        return new_state

    def calculate_results(self) -> list[PlayerResult]:
        """Aggregates all submissions, marks, and feedback into a final results list."""

        # All marking results share the same max_score structure, so use the first one
        if self.marking_results:
            first_result = next(iter(self.marking_results.values()))
            max_score = sum(section.max_score for section in first_result.sections)
        else:
            max_score = 0

        return calculate_all_results(
            players=self.players.get_all(),
            marking_results_by_author=self.marking_results,
            max_score=max_score,
        )

    def reset_to_lobby(self) -> None:
        """Resets the room back to LOBBY state for another round."""

        self._state_machine.reset_to_lobby()
        self._submissions.clear()
        self._marking_assignments.clear()
        self.marking_results.clear()
        self._phase_end_time = 0
        self.players.reset_ready_status()

    def to_snapshot(self) -> RoomSnapshot:
        """Builds a full serializable RoomSnapshot Protobuf message for broadcasting."""

        return RoomSnapshot(
            room_code=self._code,
            state=self.state,
            settings=self.settings,
            players=self.players.to_proto_list(),
            exam_pdf_uploaded=self._exam_file_bytes is not None,
            phase_end_time=self._phase_end_time,
        )
