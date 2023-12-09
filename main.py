from fastapi import FastAPI

from database import engine, Base
from user import user
from chat import socket
app = FastAPI()

app.include_router(user.router)
app.include_router(socket.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await engine.disconnect()

