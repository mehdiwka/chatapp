from sqlalchemy import Column, String, ForeignKey
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

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    user2_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    messages = relationship('Message', backref='conversation')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey('conversations.id'), nullable=False)
    content = Column(String, nullable=False)
