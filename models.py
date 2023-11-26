from sqlalchemy.orm import relationship
import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import BigInteger

from database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    number = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=True)
    username = Column(String, nullable=True, unique=True)
    name = Column(String(255), nullable=True)
    sessions = relationship('UserSession', backref='user')  # direct access to user sessions


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    device_info = Column(String)
    session_token = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    user1 = relationship('User', foreign_keys=[user1_id])  # direct access to user1

    user2_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    user2 = relationship('User', foreign_keys=[user2_id])  # direct access to user2

    messages = relationship('Message', backref='conversation')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey('conversations.id'), nullable=False)
    content = Column(String, nullable=False)
