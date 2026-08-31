import random

from utils.logger import get_logger

logger = get_logger("services.assignment")


class AssignmentError(Exception):
    """Base exception for peer assignment errors."""


def assign_peer_markers(player_ids: list[str], randomise: bool = True) -> dict[str, str]:
    """
    Assigns peer reviewers to author submissions using a circular shift algorithm.

    Returns a mapping of marker_id -> author_id.
    """

    if not player_ids:
        logger.warning("No players in the room.")
        return {}

    if len(player_ids) == 1:
        logger.warning(f"Single-player room: Player {player_ids[0]} assigned to self-review.")
        return {player_ids[0]: player_ids[0]}

    ids = random.sample(player_ids, len(player_ids)) if randomise else player_ids
    n = len(ids)
    return {ids[i]: ids[(i + 1) % n] for i in range(n)}
