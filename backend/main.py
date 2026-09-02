import asyncio
import os

import websockets
from websockets.asyncio.server import ServerConnection

from handlers.connection import handle_disconnect
from services.room_manager import RoomManager
from transport.connection_manager import ConnectionManager
from transport.context import Context
from transport.dispatcher import dispatch_message
from utils.constants import DEFAULT_HOST, DEFAULT_PORT, MAX_MESSAGE_SIZE_BYTES
from utils.logger import get_logger

logger = get_logger("main")


class PeerPapersServer:
    """Orchestrates the WebSocket server lifecycle, connection pooling, and state routing."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.room_manager = RoomManager()
        self.conn_manager = ConnectionManager()
        self._stop_event = asyncio.Event()

    async def ws_handler(self, websocket: ServerConnection) -> None:
        """Handles a single client WebSocket connection session."""

        ctx = Context(
            ws=websocket,
            room_manager=self.room_manager,
            conn_manager=self.conn_manager,
        )

        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        logger.info(f"New client connected from {client_ip}")

        try:
            async for raw_message in websocket:
                if isinstance(raw_message, str):
                    raw_message = raw_message.encode("utf-8")
                await dispatch_message(ctx, raw_message)

        except websockets.ConnectionClosedOK:
            logger.info(f"Client disconnected cleanly: {client_ip}")
        except websockets.ConnectionClosedError as e:
            logger.warning(f"Client connection closed with error: {client_ip} ({e})")
        except Exception as e:
            logger.exception(f"Unexpected connection error for {client_ip}: {e}")
        finally:
            await handle_disconnect(ctx)

    async def start(self) -> None:
        """Starts the WebSocket server and listens for incoming connections."""

        logger.info(f"Starting PeerPapers server on ws://{self.host}:{self.port}...")

        async with websockets.serve(self.ws_handler, self.host, self.port, max_size=MAX_MESSAGE_SIZE_BYTES):
            logger.info(f"PeerPapers server running and accepting connections on port {self.port}")
            await self._stop_event.wait()

        logger.info("PeerPapers server has shut down cleanly.")

    def stop(self) -> None:
        """Signals the server to stop accepting connections and terminate."""

        self._stop_event.set()


def main() -> None:
    """Configures environment, registers signal handlers, and boots the async event loop."""

    host = os.getenv("PEERPAPERS_HOST", DEFAULT_HOST)
    port = int(os.getenv("PEERPAPERS_PORT", str(DEFAULT_PORT)))

    server = PeerPapersServer(host=host, port=port)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(server.start())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received.")
    finally:
        server.stop()
        loop.close()


if __name__ == "__main__":
    main()
