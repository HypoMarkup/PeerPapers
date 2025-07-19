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
    handle_host_start,
)
from connectivity import CommunicationMedium, WebsocketMedium
from player_manager import Player
from managers import player_manager, connection_manager, state_manager, content_manager
from shared.message import (
    ClientMessageTypes,
    PlayerStatus,
    ClientMessage,
    ServerPlayersStatusBroadcast,
    ServerStateBroadcast,
    ServerState,
    ServerQuestionStageBroadcast,
)

from pydantic import ValidationError


# Server -> Clients
async def glorious_main_loop():
    while True:
        # All game logic goes here
        await sleep(5)

        if state_manager.is_in_lobby():
            player_manager.filter_players(lambda x: x.is_connected())
        else:
            to_remove = player_manager.filter_players(lambda x: x.is_initialised)
            for player in to_remove:
                # TODO: Better handling to stop players from joining after lobby
                #       Screen on frontend
                sock = player.get_sock()
                if sock is not None:
                    connection_manager.disconnect(sock)

        player_state: ServerPlayersStatusBroadcast = ServerPlayersStatusBroadcast(
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
        )

        await player_manager.broadcast(player_state.model_dump_json())

        server_state: ServerStateBroadcast = ServerStateBroadcast(
            type="state", state=state_manager.get_state()
        )
        await player_manager.broadcast(server_state.model_dump_json())

        if state_manager.get_state() == ServerState.QUESTION:
            pdf = content_manager.get_pdf()
            assert pdf is not None
            question: ServerQuestionStageBroadcast = ServerQuestionStageBroadcast(
                type="question", base64PDF=pdf, marks=10
            )
            await player_manager.broadcast(question.model_dump_json())

        print(connection_manager.active_connections, state_manager.get_state())


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
] = {"host set pdf": handle_host_set_PDF, "host start": handle_host_start}


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
        if state_manager.is_in_lobby():
            p = player_manager.get_player_by_connection(c)
            if p is not None:
                player_manager.remove_player(p)

        print(player_manager.players)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
