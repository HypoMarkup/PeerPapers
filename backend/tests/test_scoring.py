from core.player import Player
from generated.v1.models_pb2 import MarkingResult, SectionFeedback
from services.scoring import (
    calculate_all_results,
    calculate_player_result,
    calculate_section_total,
)


def test_calculate_section_total_handles_none_and_empty() -> None:
    """None or empty section lists should safely return 0.0 without errors."""

    assert calculate_section_total(None) == 0.0
    assert calculate_section_total(MarkingResult(sections=[])) == 0.0


def test_calculate_section_total_sums_scores() -> None:
    """Calculates the sum of fractional section scores."""

    marking = MarkingResult(
        sections=[
            SectionFeedback(section_index=0, score=7.5, max_score=10),
            SectionFeedback(section_index=1, score=8.0, max_score=10),
        ]
    )
    assert calculate_section_total(marking) == 15.5


def test_calculate_player_result_without_feedback() -> None:
    """Player with missing feedback receives 0.0 score and unset feedback field."""

    player = Player(name="Alice")
    result = calculate_player_result(player, feedback_received=None, max_score=20)

    assert result.player.name == "Alice"
    assert result.total_score == 0.0
    assert result.max_score == 20
    assert not result.HasField("feedback_received")


def test_calculate_all_results_ranks_leaderboard_descending() -> None:
    """Leaderboard results must be sorted with the highest total score first."""

    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    p3 = Player(name="Charlie")

    marking_map = {
        p1.id: MarkingResult(sections=[SectionFeedback(score=10.0, max_score=20)]),
        p2.id: MarkingResult(sections=[SectionFeedback(score=18.5, max_score=20)]),
        # Charlie has no feedback (None) -> 0.0
    }

    results = calculate_all_results(
        players=[p1, p2, p3],
        marking_results_by_author=marking_map,
        max_score=20,
    )

    # Bob (18.5) -> Alice (10.0) -> Charlie (0.0)
    assert [r.player.name for r in results] == ["Bob", "Alice", "Charlie"]
    assert [r.total_score for r in results] == [18.5, 10.0, 0.0]
