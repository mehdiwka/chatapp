from typing import Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db_session
from models import Conversation, Message

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, websocket: WebSocket, user_id: str):
        await websocket.close()
        self.active_connections.pop(user_id)

    def get_socket_by_user_id(self, user_id):
        user = self.active_connections.get(user_id)
        return user

    async def send_message(self, db: AsyncSession, from_user: str, to_user: str, message: str):
        to_websocket = self.active_connections.get(to_user)
        if to_websocket:
            await to_websocket.send_text(f"{from_user}: {message}")
        else:
            # Use Kafka
            producer = kafka_producer()
            producer.produce('mytopic', key=to_user, value=message, callback=delivery_report)
            producer.flush()

        await self.store_message(db, from_user, to_user, message)

    async def store_message(self, db: AsyncSession, from_user: str, to_user: str, message: str):
        async with db.begin():
            conversation = await db.execute(select(Conversation).where(
                (Conversation.user1_id == from_user) & (Conversation.user2_id == to_user) | (
                        Conversation.user1_id == to_user) & (Conversation.user2_id == from_user)))
            conversation = conversation.scalar_one_or_none()
            if conversation is None:
                conversation = Conversation(user1_id=from_user, user2_id=to_user)
                db.add(conversation)
                await db.flush()

            message = Message(conversation_id=conversation.id, content=message)
            db.add(message)
            await db.commit()


from confluent_kafka import Producer


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {}'.format(msg.topic()))


def kafka_producer():
    # Set up a Kafka producer configuration
    conf = {'bootstrap.servers': '<your_kafka_bootstrap_servers>'}

    # Create Producer instance
    p = Producer(conf)

    return p


manager = ConnectionManager()


@router.websocket_route("/ws/{user_id}")
async def manage_ws(websocket: WebSocket, user_id: str, action: str):
    if action == 'open':
        await manager.connect(websocket, user_id)
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content={"Status": f"WebSocket opened for user: {user_id}"})
    elif action == 'close':
        await manager.disconnect(websocket, user_id)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"Status": f"WebSocket closed for user: {user_id}"})
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"Status": "Invalid action"})


@router.websocket_route("/ws/send_message")
async def send_message(websocket: WebSocket, from_user: str, to_user: str, message: str,
                       db: AsyncSession = Depends(get_db_session)):
    await manager.send_message(db, from_user, to_user, message)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"Status": f"Message sent from user: {from_user} to user: {to_user}"})
