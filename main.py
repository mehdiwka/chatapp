from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from database import engine, get_db_session, Base
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import SQLAlchemyError
from routers import user

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models import User
# from schemas import UserIn
from database import get_db_session
from routers import user
app = FastAPI()

app.include_router(user.router)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await engine.disconnect()


# @app.post("/users/")
# async def create_user(user: UserIn, db: AsyncSession = Depends(get_db_session)):
#     async with db as db_session:
#         try:
#             db_user = User(number=user.number, username=user.username, name=user.name)
#             db_session.add(db_user)
#             await db_session.commit()
#             await db_session.refresh(db_user)
#             return db_user.__dict__
#         except SQLAlchemyError:
#             await db_session.rollback()
#             raise HTTPException(status_code=400, detail="Error while creating user.")

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
