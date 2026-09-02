from google.protobuf.message import DecodeError

from generated.v1.messages_pb2 import ClientMessage, ErrorCode
from generated.v1.models_pb2 import RoomState
from handlers.connection import handle_authenticate
from handlers.exam import (
    handle_force_end_exam,
    handle_request_exam_pdf,
    handle_save_progress,
    handle_start_exam,
)
from handlers.lobby import (
    handle_create_room,
    handle_join_room,
    handle_leave_room,
    handle_set_ready,
    handle_update_settings,
    handle_upload_exam,
)
from handlers.marking import (
    handle_force_end_marking,
    handle_submit_marking,
)
from transport.context import Context
from utils.logger import get_logger

logger = get_logger("transport.dispatcher")


async def dispatch_message(ctx: Context, raw_data: bytes) -> None:
    """Deserializes an incoming binary WebSocket frame into a ClientMessage and routes it."""

    try:
        client_msg = ClientMessage.FromString(raw_data)
    except DecodeError as e:
        logger.warning(f"Failed to decode Protobuf ClientMessage: {e}")
        await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Malformed Protobuf message payload.")
        return

    payload_type = client_msg.WhichOneof("payload")
    if not payload_type:
        logger.warning("Received empty ClientMessage with no payload.")
        await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Empty message payload.")
        return

    logger.debug(f"Dispatching message '{payload_type}' for player '{ctx.player.name if ctx.player else 'Anonymous'}'")

    try:
        match payload_type:
            # ─── Connection Lifecycle ───
            case "authenticate":
                await handle_authenticate(ctx, client_msg.authenticate)

            # ─── Lobby Phase ───
            case "create_room":
                await handle_create_room(ctx, client_msg.create_room)
            case "join_room":
                await handle_join_room(ctx, client_msg.join_room)
            case "leave_room":
                await handle_leave_room(ctx, client_msg.leave_room)
            case "update_settings":
                await handle_update_settings(ctx, client_msg.update_settings)
            case "set_ready":
                await handle_set_ready(ctx, client_msg.set_ready)
            case "upload_exam":
                await handle_upload_exam(ctx, client_msg.upload_exam)

            # ─── Exam Phase ───
            case "start_exam":
                await handle_start_exam(ctx, client_msg.start_exam)
            case "save_progress":
                await handle_save_progress(ctx, client_msg.save_progress)
            case "request_exam_pdf":
                await handle_request_exam_pdf(ctx, client_msg.request_exam_pdf)

            # ─── Marking Phase ───
            case "submit_marking":
                await handle_submit_marking(ctx, client_msg.submit_marking)

            # ─── Admin Phase Override ───
            case "force_end_phase":
                if ctx.room and ctx.room.state == RoomState.ROOM_STATE_EXAM:
                    await handle_force_end_exam(ctx, client_msg.force_end_phase)
                elif ctx.room and ctx.room.state == RoomState.ROOM_STATE_MARKING:
                    await handle_force_end_marking(ctx, client_msg.force_end_phase)
                else:
                    await ctx.send_error(
                        ErrorCode.ERROR_CODE_INVALID_STATE,
                        "Cannot force end phase outside EXAM or MARKING states.",
                    )

            case _:
                logger.error(f"Unhandled payload type: {payload_type}")
                await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, f"Unknown message type '{payload_type}'.")

    except Exception as e:
        logger.exception(f"Unexpected error handling '{payload_type}': {e}")
        await ctx.send_error(ErrorCode.ERROR_CODE_INTERNAL_ERROR, "An internal server error occurred.")
