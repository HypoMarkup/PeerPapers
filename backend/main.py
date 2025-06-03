from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from connectivity import ConnectionManager, WebsocketMedium
from player import Player
from message import IncomingMessage, AssignUUIDMessage
from pydantic import ValidationError

app = FastAPI()

manager = ConnectionManager()

# TODO: Build Player manager or some sort
players: list[Player] = []


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    c = WebsocketMedium(ws)
    await manager.connect(c)
    try:
        while True:
            data = await c.receive_text()
            incoming_msg = IncomingMessage.model_validate_json(data)
            if incoming_msg.type == "acquireUUID":
                p = Player(c)
                players.append(p)
                outgoing_msg = AssignUUIDMessage(type="assignUUID", uuid=p.uuid)
                await manager.send_personal_message(c, outgoing_msg.model_dump_json())
            # await manager.broadcast(f"Client says: {data}")
    except (WebSocketDisconnect, ValidationError):
        manager.disconnect(c)
        # await manager.broadcast(f"Client left the chat")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
