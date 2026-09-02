from core.player import Player
from core.room import RoomStateError
from generated.v1.messages_pb2 import (
    AuthSuccess,
    CreateRoom,
    ErrorCode,
    JoinRoom,
    LeaveRoom,
    RoomCreated,
    RoomStateUpdate,
    ServerMessage,
    SetReady,
    UpdateSettings,
    UploadExam,
)
from services.room_manager import RoomCodeCollisionError
from transport.context import Context
from utils.logger import get_logger

logger = get_logger("handlers.lobby")


async def handle_create_room(ctx: Context, msg: CreateRoom) -> None:
    """Handles creating a new room, initializing the admin player, and returning session credentials."""

    if not msg.player_name.strip():
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Player name cannot be empty.")

    if not msg.password.strip():
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Room password cannot be empty.")

    if not msg.HasField("settings"):
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Room settings are required.")

    if msg.settings.exam_duration_mins <= 0:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Exam duration must be greater than 0.")

    admin = Player(name=msg.player_name.strip(), is_admin=True)

    try:
        room = ctx.room_manager.create_room(
            password=msg.password,
            admin_player=admin,
            settings=msg.settings,
        )
    except RoomCodeCollisionError:
        logger.error("Failed to generate unique room code.")
        return await ctx.send_error(ErrorCode.ERROR_CODE_INTERNAL_ERROR, "Failed to create room. Please try again.")

    ctx.bind_session(admin, room)

    await ctx.send(ServerMessage(
        auth_success=AuthSuccess(
            session_token=admin.session_token,
            player_id=admin.id,
        ),
    ))
    await ctx.send(ServerMessage(
        room_created=RoomCreated(room_code=room.code),
    ))
    await ctx.broadcast_room_snapshot()


async def handle_join_room(ctx: Context, msg: JoinRoom) -> None:
    """Handles a player joining an existing room after validating password and name availability."""

    if not msg.player_name.strip():
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Player name cannot be empty.")

    room = ctx.room_manager.get_room(msg.room_code)
    if room is None:
        return await ctx.send_error(ErrorCode.ERROR_CODE_ROOM_NOT_FOUND, "Room not found.")

    if not room.verify_password(msg.password):
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_PASSWORD, "Incorrect room password.")

    if room.players.is_name_taken(msg.player_name.strip()):
        return await ctx.send_error(ErrorCode.ERROR_CODE_NAME_TAKEN, "That name is already taken in this room.")

    player = Player(name=msg.player_name.strip())
    room.players.add_player(player)
    ctx.bind_session(player, room)

    await ctx.send(ServerMessage(
        auth_success=AuthSuccess(
            session_token=player.session_token,
            player_id=player.id,
        ),
    ))
    await ctx.broadcast_room_snapshot()


async def handle_leave_room(ctx: Context, msg: LeaveRoom) -> None:
    """Handles a player voluntarily leaving a room, performing host migration if admin leaves."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.player is not None and ctx.room is not None

    room = ctx.room
    player_id = ctx.player.id

    _ = room.players.remove_player(player_id)
    ctx.unbind_session()

    # Broadcast updated snapshot to remaining players (or delete room if everyone has left)
    if room.players.count() > 0:
        snapshot_message = ServerMessage(
            room_state_update=RoomStateUpdate(room=room.to_snapshot()),
        )
        await ctx.conn_manager.broadcast_to_players(
            player_ids=room.players.get_all_ids(),
            message=snapshot_message,
        )
    else:
        _ = ctx.room_manager.remove_room(room.code)


async def handle_update_settings(ctx: Context, msg: UpdateSettings) -> None:
    """Handles admin updating room configuration (e.g. exam duration) during the LOBBY phase."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.room is not None

    if not ctx.is_admin:
        return await ctx.send_error(ErrorCode.ERROR_CODE_NOT_ADMIN, "Only the admin can update settings.")

    if not msg.HasField("settings"):
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Settings are required.")

    if msg.settings.exam_duration_mins <= 0:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Exam duration must be greater than 0.")

    try:
        ctx.room.update_settings(msg.settings)
    except RoomStateError:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_STATE, "Settings can only be updated in the lobby.")

    await ctx.broadcast_room_snapshot()


async def handle_set_ready(ctx: Context, msg: SetReady) -> None:
    """Handles a player toggling their ready status in the lobby."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.player is not None

    ctx.player.is_ready = msg.is_ready
    await ctx.broadcast_room_snapshot()


async def handle_upload_exam(ctx: Context, msg: UploadExam) -> None:
    """Handles admin uploading the exam PDF file during the LOBBY phase."""

    if not ctx.is_authenticated:
        return await ctx.send_error(ErrorCode.ERROR_CODE_UNAUTHORIZED, "You are not in a room.")
    assert ctx.room is not None

    if not ctx.is_admin:
        return await ctx.send_error(ErrorCode.ERROR_CODE_NOT_ADMIN, "Only the admin can upload the exam.")

    if not msg.filename:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Exam filename cannot be empty.")

    if not msg.file_data:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_ARGUMENT, "Exam file data cannot be empty.")

    try:
        ctx.room.set_exam_pdf(
            filename=msg.filename,
            file_bytes=msg.file_data,
        )
    except RoomStateError:
        return await ctx.send_error(ErrorCode.ERROR_CODE_INVALID_STATE, "Exam PDF can only be uploaded in the lobby.")

    await ctx.broadcast_room_snapshot()
