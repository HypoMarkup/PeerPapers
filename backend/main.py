from asyncio import create_task, sleep, CancelledError
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from validators import is_valid_name
from game_state import GameState
from connectivity import ConnectionManager, WebsocketMedium
from player import Player, PlayerManager
from shared.message import (
    ServerFailedReconnectionMessage,
    ClientReconnectMessage,
    ClientMessage,
    ServerUUIDAssignmentMessage,
    ServerMessage,
    ServerSendPlayerData,
    PlayerData,
    ClientSetPlayerDataMessage,
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
        p: Player | None = None
        while True:
            print(player_manager.players)
            data = await c.receive_text()
            incoming_msg = ClientMessage.model_validate_json(data)
            match incoming_msg.type:
                case "initial connect":
                    if p != None:
                        raise WebSocketDisconnect(code=1003, reason="Already connected")
                    p = Player(c)
                    player_manager.add_player(p)
                    outgoing_msg = ServerUUIDAssignmentMessage(
                        type="uuid assignment", uuid=p.uuid
                    )
                    await connection_manager.send_personal_message(
                        c, outgoing_msg.model_dump_json()
                    )
                case "reconnect":
                    if p != None:
                        raise WebSocketDisconnect(code=1003, reason="Already connected")

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
                case "get player data":
                    if p == None:
                        raise WebSocketDisconnect(code=1003, reason="Not connected")

                    if p.data == None:
                        data = PlayerData(name="", picture="")
                        outgoing_msg = ServerSendPlayerData(
                            type="send player data", data=data
                        )
                    else:
                        outgoing_msg = ServerSendPlayerData(
                            type="send player data", data=p.data
                        )
                    await connection_manager.send_personal_message(
                        c, outgoing_msg.model_dump_json()
                    )
                case "set player data":
                    if p == None:
                        raise WebSocketDisconnect(code=1003, reason="Not connected")

                    incoming_msg = ClientSetPlayerDataMessage.model_validate_json(data)
                    new_name = incoming_msg.data.name
                    if (
                        is_valid_name(new_name)
                        and player_manager.get_player(
                            lambda x: x.data != None and x.data.name == new_name
                        )
                        == None
                    ):
                        if p.data is None:
                            p.data = PlayerData(
                                name=new_name, picture=incoming_msg.data.picture
                            )
                        else:
                            p.data.name = new_name
                            p.data.picture = incoming_msg.data.picture
                    else:
                        outgoing_msg = ServerMessage(type="invalid player data")
                        await connection_manager.send_personal_message(
                            c, outgoing_msg.model_dump_json()
                        )

                case _:
                    # What are doing
                    raise WebSocketDisconnect(code=1002, reason="Invalid message type")

    except (WebSocketDisconnect, ValidationError):
        connection_manager.disconnect(c)

        # Reconnection not allowed in lobby
        if state == GameState.Lobby:
            p = player_manager.get_player_by_connection(c)
            if p is not None:
                player_manager.remove_player(p)

        print(player_manager.players)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
