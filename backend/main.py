# import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from connectivity import ConnectionManager, WebsocketMedium

app = FastAPI()

manager = ConnectionManager()

# async def main_loop():
#     while True:
#         print("Running main logic loop...")
#         # do checks here

#         # we fs need this for timer
#         await asyncio.sleep(1)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    c = WebsocketMedium(ws)
    await manager.connect(c)
    try:
        while True:
            data = await c.receive_text()
            await manager.broadcast(f"Client {manager.getID(c)} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(c)
        await manager.broadcast(f"Client {manager.getID(c)} left the chat")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}
