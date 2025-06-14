from asyncio import create_task, sleep, CancelledError
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game_state import GameState
from connectivity import ConnectionManager, WebsocketMedium
from player import Player, PlayerManager
from backend.shared.message import (
    ServerFailedReconnectionMessage,
    ClientReconnectMessage,
    ClientMessage,
    ServerUUIDAssignmentMessage,
    ServerMessage,
)
from pydantic import ValidationError

connection_manager = ConnectionManager()
player_manager = PlayerManager()

state: GameState = GameState.Lobby


async def glorious_main_loop():
    while True:
        # All game logic goes here
        await sleep(5)
        print("hi")


@asynccontextmanager
async def start_main_loop(app: FastAPI):
    task = create_task(glorious_main_loop())
    yield
    task.cancel()
    try:
        await task
    except CancelledError:
        pass


app = FastAPI(lifespan=start_main_loop)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    c = WebsocketMedium(ws)
    await connection_manager.connect(c)
    try:
        p = None
        while True:
            print(player_manager.players)
            data = await c.receive_text()
            incoming_msg = ClientMessage.model_validate_json(data)
            match incoming_msg.type:
                case "initial connect":
                    p = Player(c)
                    player_manager.add_player(p)
                    outgoing_msg = ServerUUIDAssignmentMessage(
                        type="uuid assignment", uuid=p.uuid
                    )
                    await connection_manager.send_personal_message(
                        c, outgoing_msg.model_dump_json()
                    )
                case "reconnect":
                    incoming_msg = ClientReconnectMessage.model_validate_json(data)
                    p = player_manager.reconnect_player_via_UUID(incoming_msg.uuid, c)
                    if p is not None:
                        outgoing_msg = ServerMessage(type="successful reconnect")
                        await connection_manager.send_personal_message(
                            c, outgoing_msg.model_dump_json()
                        )
                    else:
                        outgoing_msg = ServerFailedReconnectionMessage(
                            type="failed reconnect",
                            reason="invalid uuid",
                            shouldReset=(state == GameState.Lobby),
                        )
                        await connection_manager.send_personal_message(
                            c, outgoing_msg.model_dump_json()
                        )
                        raise WebSocketDisconnect(code=1003, reason="Invalid UUID")

    except (WebSocketDisconnect, ValidationError):
        connection_manager.disconnect(c)
        print(player_manager.players)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
