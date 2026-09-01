from generated.v1.messages_pb2 import Authenticate, AuthSuccess, ErrorCode, ServerMessage
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

            auth_success = ServerMessage(
                auth_success=AuthSuccess(
                    session_token=msg.session_token,
                    player_id=player.id
                )
            )
            await ctx.send(auth_success)

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
