from generated.v1.messages_pb2 import (
    Authenticate,
    AuthSuccess,
    ErrorCode,
    MarkingAssignment,
    ResultsBroadcast,
    ReturnProgress,
    ServerMessage,
)
from generated.v1.models_pb2 import RoomState, Submission
from transport.context import Context
from utils.logger import get_logger

logger = get_logger("handlers.connection")


async def handle_authenticate(ctx: Context, msg: Authenticate) -> None:
    """Handles reconnection and session re-binding via a client session token."""

    for room in ctx.room_manager.list_rooms():
        player = room.players.get_by_session_token(msg.session_token)

        if player is not None:
            player.is_connected = True
            ctx.bind_session(player, room)

            await ctx.send(ServerMessage(
                auth_success=AuthSuccess(
                    session_token=msg.session_token,
                    player_id=player.id,
                ),
            ))

            # If reconnecting during EXAM, send the user's work so far back to them
            if room.state == RoomState.ROOM_STATE_EXAM:
                submission = room.get_submission(player.id)
                if submission is not None:
                    await ctx.send(ServerMessage(
                        return_progress=ReturnProgress(
                            submission=submission
                        )
                    ))

            # If reconnecting during MARKING, deliver their assigned paper
            elif room.state == RoomState.ROOM_STATE_MARKING:
                author_id = room.get_assigned_author_id(player.id)
                if author_id is not None:
                    submission = room.get_submission(author_id) or Submission(player_id=author_id, sections=[])
                    author = room.players.get_by_id(author_id)
                    author_name = author.name if author else "N/A"
                    await ctx.send(ServerMessage(
                        marking_assignment=MarkingAssignment(
                            submission=submission,
                            author_name=author_name,
                        ),
                    ))

            # If reconnecting during RESULTS, deliver the final leaderboard
            elif room.state == RoomState.ROOM_STATE_RESULTS:
                results = room.calculate_results()
                await ctx.send(ServerMessage(
                    results_broadcast=ResultsBroadcast(results=results),
                ))

            await ctx.broadcast_room_snapshot()
            return

    await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "Invalid or expired session token")


async def handle_disconnect(ctx: Context) -> None:
    """Handles client WebSocket disconnection, updates player state, and notifies the room."""

    if ctx.player is None:
        logger.warning("Attempted to disconnect non-existent player.")
        return

    ctx.player.is_connected = False
    await ctx.broadcast_room_snapshot()
    ctx.unbind_session()
