from asyncio import create_task, sleep, CancelledError
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from connectivity import ConnectionManager, WebsocketMedium
from player import Player, PlayerManager
from message import (
    ReconnectMessage,
    IncomingMessage,
    UUIDAssignmentMessage,
    OutgoingMessage,
)
from pydantic import ValidationError


connection_manager = ConnectionManager()
player_manager = PlayerManager()


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
            incoming_msg = IncomingMessage.model_validate_json(data)
            if incoming_msg.type == "initial-connect":
                p = Player(c)
                player_manager.add_player(p)
                outgoing_msg = UUIDAssignmentMessage(
                    type="uuid-assignment", uuid=p.uuid
                )
                await connection_manager.send_personal_message(
                    c, outgoing_msg.model_dump_json()
                )
            elif incoming_msg.type == "reconnect":
                incoming_msg = ReconnectMessage.model_validate_json(data)
                p = player_manager.reconnect_player_via_UUID(incoming_msg.uuid, c)
                if p is not None:
                    outgoing_msg = OutgoingMessage(type="successful-reconnect")
                    await connection_manager.send_personal_message(
                        c, outgoing_msg.model_dump_json()
                    )
                else:
                    outgoing_msg = OutgoingMessage(type="failed-reconnect")
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
