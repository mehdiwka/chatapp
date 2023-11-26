import secrets
from typing import List

import bcrypt
from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db_session
from models import User, UserSession
from .schemas import Login, UserSetPassword, UserSetProfile, UserForgetPassword, Register, SessionBase

router = APIRouter()
oauth2_scheme = HTTPBearer()


def create_session_token():
    return secrets.token_hex(16)


def get_current_user_token(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    return token.credentials


async def get_current_user(db: AsyncSession = Depends(get_db_session),
                           session_token: str = Depends(get_current_user_token)):
    async with db as session:  # this context manager ensures the session is closed after use
        user_session_result = await session.execute(
            select(UserSession).where(UserSession.session_token == session_token))
        user_session = user_session_result.scalars().first()
        if user_session:
            user_result = await session.execute(select(User).where(User.id == user_session.user_id))
            user = user_result.scalars().first()
        else:
            user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post('/register')
async def register_new_user(user_in: Register, db: AsyncSession = Depends(get_db_session)):
    if user_in.otp != "1234":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP.")
    async with db as session:
        user_result = await session.execute(select(User).where(User.number == user_in.number))
        user = user_result.scalar_one_or_none()
        if user:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number already registered.")
        user = User(number=user_in.number)
        session.add(user)
        await session.flush()
        session_token = create_session_token()
        user_session = UserSession(user_id=user.id, session_token=session_token)
        session.add(user_session)
        await session.commit()

    return {"status": "Success", "session_token": session_token}


@router.post('/login')
async def login(user_in: Login):
    if user_in.otp != "1234":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP.")

    async with get_db_session() as db:
        user_result = await db.execute(select(User).filter(User.number == user_in.number))
        user = user_result.scalar_one_or_none()

        if not user or not bcrypt.checkpw(user_in.password.encode(), user.hashed_password.encode("utf-8")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP or password")

        session_token = create_session_token()
        user_session = UserSession(user_id=user.id, session_token=session_token)
        db.add(user_session)
        await db.commit()
    return {"session_token": session_token}


@router.post('/set_password')
async def set_password(user_in: UserSetPassword, current_user: User = Depends(get_current_user)):
    async with get_db_session() as db:
        hashed_password = bcrypt.hashpw(user_in.new_password.encode('utf-8'), bcrypt.gensalt())
        current_user.hashed_password = hashed_password.decode()

        db.add(current_user)
        await db.flush()
        await db.commit()

    return {"status": "Success"}


@router.post('/set_profile')
async def set_profile(user_in: UserSetProfile, current_user: User = Depends(get_current_user)):
    async with get_db_session() as db:
        user_with_same_username_result = await db.execute(select(User).where(User.username == user_in.username))
        user_with_same_username = user_with_same_username_result.scalar_one_or_none()
        if user_with_same_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
        current_user.username = user_in.username
        current_user.name = user_in.name
        db.add(current_user)
        await db.commit()
    return {"status": "Success"}


@router.post('/forget_password', status_code=status.HTTP_202_ACCEPTED)
async def forget_password(user_in: UserForgetPassword, db: AsyncSession = Depends(get_db_session)):
    user = await db.execute(select(User).where(User.number == user_in.number))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found.")
    user.hashed_password = bcrypt.hashpw(user_in.new_password.encode('utf-8'), bcrypt.gensalt())

    await db.commit()
    return {"status": "Success"}


@router.get("/user/{user_id}/sessions", response_model=List[str])
async def get_user_sessions(user_id: int, current_user: User = Depends(get_current_user)):
    async with get_db_session() as db:
        result = await db.execute(select(UserSession.session_token).where(UserSession.user_id == user_id))
        session_tokens = result.scalars().all()
        return session_tokens


@router.delete("/session/{session_token}")
async def delete_session(session_token: str, current_user: User = Depends(get_current_user)):
    async with get_db_session() as db:
        result = await db.execute(select(UserSession).where(UserSession.session_token == session_token))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        await db.delete(session)
        await db.commit()
    return {"status": "Success"}
