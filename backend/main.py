from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from connectivity import ConnectionManager, WebsocketMedium
from player import Player, PlayerManager
from message import (
    CheckUUIDMessage,
    IncomingMessage,
    AssignUUIDMessage,
    OutgoingMessage,
)
from pydantic import ValidationError

app = FastAPI()

connection_manager = ConnectionManager()
player_manager = PlayerManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    c = WebsocketMedium(ws)
    await connection_manager.connect(c)
    try:
        while True:
            print(player_manager.players)
            data = await c.receive_text()
            incoming_msg = IncomingMessage.model_validate_json(data)
            if incoming_msg.type == "acquireUUID":
                p = Player(c)
                player_manager.add_player(p)
                outgoing_msg = AssignUUIDMessage(type="assignUUID", uuid=p.uuid)
                await connection_manager.send_personal_message(
                    c, outgoing_msg.model_dump_json()
                )
            elif incoming_msg.type == "checkUUID":
                incoming_msg = CheckUUIDMessage.model_validate_json(data)
                if player_manager.reconnect_player_via_UUID(incoming_msg.uuid, c):
                    outgoing_msg = OutgoingMessage(type="validUUID")
                else:
                    outgoing_msg = OutgoingMessage(type="invalidUUID")
                await connection_manager.send_personal_message(
                    c, outgoing_msg.model_dump_json()
                )

                pass

    except (WebSocketDisconnect, ValidationError):
        connection_manager.disconnect(c)
        print(player_manager.players)
        # await manager.broadcast(f"Client left the chat")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
