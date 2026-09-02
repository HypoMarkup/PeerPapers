import asyncio
from unittest.mock import AsyncMock

from websockets.exceptions import ConnectionClosedOK

from core.player import Player
from generated.v1.messages_pb2 import (
    AuthSuccess,
    ServerMessage,
)
from services.room_manager import RoomManager
from transport.connection_manager import ConnectionManager
from transport.context import Context


class FakeWebSocket:
    """Fake WebSocket connection recording sent binary payloads for testing."""

    def __init__(self) -> None:
        self.sent_messages: list[ServerMessage] = []

    async def send(self, data: bytes) -> None:
        msg = ServerMessage.FromString(data)
        self.sent_messages.append(msg)


# ─── ConnectionManager Tests ───


def test_connection_manager_broadcast_with_exclusion() -> None:
    """Broadcasting excludes the specified player ID and delivers to remaining connected players."""

    async def run() -> None:
        cm = ConnectionManager()
        ws_p1 = FakeWebSocket()
        ws_p2 = FakeWebSocket()
        ws_p3 = FakeWebSocket()

        cm.register("p1", ws_p1)  # type: ignore[arg-type]
        cm.register("p2", ws_p2)  # type: ignore[arg-type]
        cm.register("p3", ws_p3)  # type: ignore[arg-type]

        msg = ServerMessage(auth_success=AuthSuccess(session_token="token123", player_id="p1"))

        # Broadcast to all 3 players, but exclude p1
        await cm.broadcast_to_players(
            player_ids=["p1", "p2", "p3"],
            message=msg,
            exclude_player_id="p1",
        )

        assert len(ws_p1.sent_messages) == 0
        assert len(ws_p2.sent_messages) == 1
        assert len(ws_p3.sent_messages) == 1

    asyncio.run(run())


def test_connection_manager_broadcast_skips_unregistered_players() -> None:
    """Broadcasting safely skips players who are in the room list but not currently connected."""

    async def run() -> None:
        cm = ConnectionManager()
        ws_p1 = FakeWebSocket()

        cm.register("p1", ws_p1)  # type: ignore[arg-type]
        # "p2" is not registered (offline)

        msg = ServerMessage(auth_success=AuthSuccess(session_token="tok", player_id="p1"))
        await cm.broadcast_to_players(
            player_ids=["p1", "p2"],
            message=msg,
        )

        assert len(ws_p1.sent_messages) == 1

    asyncio.run(run())


def test_connection_manager_send_closed_socket_auto_unregisters() -> None:
    """Sending to a closed WebSocket logs a warning and automatically unregisters the dead socket."""

    async def run() -> None:
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send.side_effect = ConnectionClosedOK(rcvd=None, sent=None)

        cm.register("p1", mock_ws)
        assert cm.is_player_connected("p1") is True

        msg = ServerMessage(auth_success=AuthSuccess(session_token="tok", player_id="p1"))
        await cm.send_to_player("p1", msg)

        # ConnectionManager must have auto-unregistered the dead socket
        assert cm.is_player_connected("p1") is False

    asyncio.run(run())


def test_connection_manager_send_timeout_auto_unregisters() -> None:
    """Sending to a hung WebSocket that times out automatically unregisters the socket."""

    async def run() -> None:
        cm = ConnectionManager()

        # A socket that never finishes sending (hangs forever)
        async def hanging_send(data: bytes) -> None:
            await asyncio.sleep(100)

        mock_ws = AsyncMock()
        mock_ws.send.side_effect = hanging_send

        cm.register("p1", mock_ws)
        assert cm.is_player_connected("p1") is True

        # Temporarily test with a short wait to verify timeout handling
        # ConnectionManager will catch TimeoutError, unregister p1, and exit cleanly
        from unittest.mock import patch

        with patch("transport.connection_manager.DEFAULT_SEND_TIMEOUT", 0.05):
            msg = ServerMessage(auth_success=AuthSuccess(session_token="tok", player_id="p1"))
            await cm.send_to_player("p1", msg)

        assert cm.is_player_connected("p1") is False

    asyncio.run(run())


# ─── Context Tests ───


def test_context_broadcast_when_unbound_does_not_crash() -> None:
    """Broadcasting from an unauthenticated context with no bound room safely logs and returns."""

    async def run() -> None:
        fake_ws = FakeWebSocket()
        ctx = Context(ws=fake_ws, room_manager=RoomManager(), conn_manager=ConnectionManager())  # type: ignore[arg-type]

        # Should not raise exception
        await ctx.broadcast_room_snapshot()
        msg = ServerMessage(auth_success=AuthSuccess(session_token="tok", player_id="p1"))
        await ctx.broadcast_to_room(msg)

        assert len(fake_ws.sent_messages) == 0

    asyncio.run(run())


def test_context_send_unauthenticated_direct_socket() -> None:
    """Sending before authentication transmits directly over the raw WebSocket socket."""

    async def run() -> None:
        fake_ws = FakeWebSocket()
        ctx = Context(ws=fake_ws, room_manager=RoomManager(), conn_manager=ConnectionManager())  # type: ignore[arg-type]

        assert ctx.player is None
        msg = ServerMessage(auth_success=AuthSuccess(session_token="tok", player_id="p1"))
        await ctx.send(msg)

        assert len(fake_ws.sent_messages) == 1
        assert fake_ws.sent_messages[0].auth_success.session_token == "tok"

    asyncio.run(run())
