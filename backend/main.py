from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def send_personal_message(self, message: str, ws: WebSocket):
        await ws.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def getID(self, ws: WebSocket):
        return self.active_connections.index(ws)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", ws)
            await manager.broadcast(f"Client {manager.getID(ws)} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
        await manager.broadcast(f"Client {manager.getID(ws)} left the chat")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
