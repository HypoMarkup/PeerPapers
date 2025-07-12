from asyncio import create_task, sleep, CancelledError
from contextlib import asynccontextmanager
from typing import Callable, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from message_handlers import (
    handle_get_player_data,
    handle_initial_connect,
    handle_reconnect,
    handle_set_player_data,
    handle_host_set_PDF,
)
from connectivity import CommunicationMedium, WebsocketMedium
from player import Player
from managers import player_manager, connection_manager, state
from shared.message import (
    ClientMessageTypes,
    PlayerStatus,
    ClientMessage,
    ServerPlayersStatusBroadcast,
    ServerState,
)
from pydantic import ValidationError
from helper import isStateLobby


# Server -> Clients
async def glorious_main_loop():
    while True:
        # All game logic goes here
        await sleep(5)

        if isStateLobby(state):
            player_manager.filter_players(lambda x: x.is_connected())

        outgoing_msg: ServerPlayersStatusBroadcast = ServerPlayersStatusBroadcast(
            type="players status",
            status=list(
                map(
                    lambda x: PlayerStatus(
                        name=x.name,
                        pictureURL=x.pictureURL,
                        isConnected=x.is_connected(),
                        isHost=x == player_manager.get_host(),
                    ),
                    filter(
                        lambda x: len(x.name) != 0,
                        player_manager.players,
                    ),
                )
            ),
            state=state,
        )

        print(connection_manager.active_connections)
        await connection_manager.broadcast(outgoing_msg.model_dump_json())


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

unauthenticated_handlers: dict[
    ClientMessageTypes,
    Callable[
        [str, Optional[Player], CommunicationMedium],
        tuple[Optional[Player], Optional[str], Optional[int], Optional[str]],
    ],
] = {"initial connect": handle_initial_connect, "reconnect": handle_reconnect}

authenticated_handlers: dict[
    ClientMessageTypes,
    Callable[
        [str, Player],
        tuple[Optional[str], Optional[int], Optional[str]],
    ],
] = {
    "get player data": handle_get_player_data,
    "set player data": handle_set_player_data,
}

host_handlers: dict[
    ClientMessageTypes,
    Callable[
        [str, Player],
        tuple[Optional[str], Optional[int], Optional[str]],
    ],
] = {
    "host set pdf": handle_host_set_PDF,
}


# Client -> Server
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    c = WebsocketMedium(ws)
    await connection_manager.connect(c)
    try:
        p: Optional[Player] = None
        while True:
            print(player_manager.players)
            data = await c.receive_text()
            incoming_msg = ClientMessage.model_validate_json(data)
            if incoming_msg.type in unauthenticated_handlers:
                p, outgoing_msg, code, reason = unauthenticated_handlers[
                    incoming_msg.type
                ](data, p, c)
            else:
                if p == None:
                    outgoing_msg, code, reason = (
                        None,
                        3000,
                        "Connection is not associated with a player",
                    )
                elif incoming_msg.type in authenticated_handlers:
                    outgoing_msg, code, reason = authenticated_handlers[
                        incoming_msg.type
                    ](data, p)
                elif incoming_msg.type in host_handlers:
                    if player_manager.get_host() == p:
                        outgoing_msg, code, reason = host_handlers[incoming_msg.type](
                            data, p
                        )
                    else:
                        outgoing_msg, code, reason = (
                            None,
                            3000,
                            "Player is not the host",
                        )
                else:
                    outgoing_msg, code, reason = (None, 1002, "Unknown message type")
            if outgoing_msg != None:
                await connection_manager.send_personal_message(c, outgoing_msg)
            if code != None and reason != None:
                await c.close(code, reason)
                raise WebSocketDisconnect(code=code, reason=reason)

    except WebSocketDisconnect as e:
        print(e.code, e.reason)
    except ValidationError as e:
        print(e.json())
    finally:

        connection_manager.disconnect(c)

        # Reconnection not allowed in lobby
        if isStateLobby(state):
            p = player_manager.get_player_by_connection(c)
            if p is not None:
                player_manager.remove_player(p)

        print(player_manager.players)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
