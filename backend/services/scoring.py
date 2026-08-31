from core.player import Player
from generated.v1.models_pb2 import MarkingResult, PlayerResult
from utils.logger import get_logger

logger = get_logger("services.scoring")


class ScoringError(Exception):
    """Base exception for scoring calculation errors."""


def calculate_section_total(marking_result: MarkingResult | None) -> float:
    """Sums the scores awarded across all sections in a marking result."""

    if marking_result is None:
        return 0.0
    return sum(section.score for section in marking_result.sections)


def calculate_player_result(
    player: Player,
    feedback_received: MarkingResult | None,
    max_score: int,
) -> PlayerResult:
    """Calculates the final score and packages the feedback for a single player."""

    total_score = calculate_section_total(feedback_received)

    result = PlayerResult(
        player=player.to_proto(),
        total_score=total_score,
        max_score=max_score,
    )
    if feedback_received is not None:
        result.feedback_received.CopyFrom(feedback_received)
    else:
        logger.warning(f"No feedback received for player {player.name}.")

    return result


def calculate_all_results(
    players: list[Player],
    marking_results_by_author: dict[str, MarkingResult],
    max_score: int,
) -> list[PlayerResult]:
    """Calculates results for all players and returns them sorted by total score descending."""

    results = [
        calculate_player_result(
            player=player,
            feedback_received=marking_results_by_author.get(player.id),
            max_score=max_score,
        )
        for player in players
    ]

    # Sort results by highest score first
    results.sort(key=lambda r: r.total_score, reverse=True)
    return results
