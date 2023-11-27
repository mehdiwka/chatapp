from typing import List

from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect

from database import engine, Base
from user import  user

app = FastAPI()

app.include_router(user.router)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await engine.disconnect()


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#
#     async def broadcast(self, data: str):
#         for connection in self.active_connections:
#             await connection.send_text(data)
#
#
# manager = ConnectionManager()
#
#
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.broadcast(data)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast("Client left the chat.")
