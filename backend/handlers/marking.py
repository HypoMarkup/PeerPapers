from core.room import RoomError, RoomStateError
from core.state_machine import StateMachineError
from generated.v1.messages_pb2 import (
    ErrorCode,
    ForceEndPhase,
    ResultsBroadcast,
    ServerMessage,
    SubmitMarking,
)
from generated.v1.models_pb2 import RoomState
from transport.context import Context
from utils.logger import get_logger

logger = get_logger("handlers.marking")


async def handle_submit_marking(ctx: Context, msg: SubmitMarking) -> None:
    """Handles a peer reviewer submitting marks and feedback for their assigned paper."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.player is not None and ctx.room is not None

    if not msg.HasField("result"):
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Marking result data is required.")

    try:
        ctx.room.submit_marking(marker_id=ctx.player.id, result=msg.result)
    except RoomStateError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_STATE, str(e))
    except RoomError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNASSIGNED_MARKER, str(e))

    # If all peer reviewers have completed their marking, advance to RESULTS automatically
    if ctx.room.all_marking_submitted():
        try:
            ctx.room.end_marking()
        except StateMachineError as e:
            return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_STATE, str(e))

        results = ctx.room.calculate_results()
        await ctx.broadcast_to_room(ServerMessage(
            results_broadcast=ResultsBroadcast(results=results)
        ))
        await ctx.broadcast_room_snapshot()
    else:
        await ctx.broadcast_room_snapshot()


async def handle_force_end_marking(ctx: Context, msg: ForceEndPhase) -> None:
    """Handles admin ending the marking phase and transitioning from MARKING to RESULTS."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.room is not None

    if not ctx.is_admin:
        return await ctx.send_error(ErrorCode.ERROR_CODE_NOT_ADMIN, "Only the admin can end marking.")

    if ctx.room.state != RoomState.ROOM_STATE_MARKING:
        return await ctx.send_error(
            ErrorCode.ERROR_CODE_INVALID_STATE,
            f"Cannot end marking from {ctx.room.state}.",
        )

    try:
        ctx.room.force_next_phase()
    except StateMachineError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_STATE, str(e))

    # Calculate final results and broadcast leaderboard to all players
    results = ctx.room.calculate_results()
    await ctx.broadcast_to_room(ServerMessage(
        results_broadcast=ResultsBroadcast(results=results)
    ))
    await ctx.broadcast_room_snapshot()
