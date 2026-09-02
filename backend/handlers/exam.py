from core.room import RoomPhaseError
from core.state_machine import (
    ExamNotUploadedError,
    GuardConditionFailedError,
    PlayersNotReadyError,
    StateMachineError,
)
from generated.v1.messages_pb2 import (
    ErrorCode,
    ExamPdfContent,
    RequestExamPdf,
    SaveProgress,
    ServerMessage,
    StartExam,
)
from transport.context import Context
from utils.logger import get_logger

logger = get_logger("handlers.exam")


async def handle_start_exam(ctx: Context, msg: StartExam) -> None:
    """Handles admin starting the exam, transitioning room state from LOBBY to EXAM."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.room is not None

    if not ctx.is_admin:
        return await ctx.send_error(ErrorCode.ERROR_CODE_NOT_ADMIN, "Only the admin can start the exam.")

    try:
        ctx.room.start_exam()
    except PlayersNotReadyError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_PLAYERS_NOT_READY, str(e))
    except ExamNotUploadedError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_EXAM_NOT_UPLOADED, str(e))
    except GuardConditionFailedError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, str(e))
    except (StateMachineError, RoomPhaseError) as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_PHASE, str(e))

    await ctx.broadcast_room_snapshot()


async def handle_save_progress(ctx: Context, msg: SaveProgress) -> None:
    """Handles autosaving a student's answer text or whiteboard progress for a section."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.player is not None and ctx.room is not None

    if not msg.HasField("section"):
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Submission section data is required.")

    try:
        ctx.room.save_progress(player_id=ctx.player.id, section=msg.section)
    except RoomPhaseError as e:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_PHASE, str(e))


async def handle_request_exam_pdf(ctx: Context, msg: RequestExamPdf) -> None:
    """Handles delivering the uploaded exam PDF bytes to a connected student."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.room is not None

    pdf_data = ctx.room.get_exam_pdf()

    if pdf_data is None:
        return await ctx.send_error(ErrorCode.ERROR_CODE_EXAM_NOT_UPLOADED, "No exam PDF has been uploaded for this room.")

    filename, file_bytes = pdf_data
    await ctx.send(ServerMessage(
        exam_pdf_content=ExamPdfContent(
            filename=filename,
            file_data=file_bytes,
        ),
    ))
