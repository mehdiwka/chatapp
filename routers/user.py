from datetime import timedelta, datetime

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db_session
from models import User
from .schemas import UserIn, UserSetPassword, UserSetProfile, UserForgetPassword

router = APIRouter()

SECRET_KEY = "k4M/NBCzlNcpG0w3ZyRgOyEbx67t6ebr3g2Sw1Tl1ReRCI/OoShQ0HRH/JwPJKJz"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def authenticate_user(db, number: str, password: str):
    user = db.execute(select(User).filter(User.number == number)).scalars().one()
    if not user:
        return False
    if bcrypt.checkpw(password.encode(), user.hashed_password.decode()):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(db: AsyncSession = Depends(get_db_session), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        number: str = payload.get("sub")
        if number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.execute(select(User).filter(User.number == number)).scalars().first()
    if user is None:
        raise credentials_exception
    return user


@router.post('/register')
async def register_new_user(user_in: UserIn, db: AsyncSession = Depends(get_db_session)):
    if user_in.otp_or_password != "1234":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP.")
    async with db as session:
        user_result = await session.execute(select(User).where(User.number == user_in.number))
        user = user_result.scalar_one_or_none()
        if user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number already registered.")
        user = User(number=user_in.number)
        session.add(user)
        await session.commit()
    return {"status": "Success"}


@router.post('/login')
async def login(user_in: UserIn, db: AsyncSession = Depends(get_db_session)):
    user = authenticate_user(db, user_in.number, user_in.otp_or_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.number}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/set_password')
async def set_password(user_in: UserSetPassword, current_user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db_session)):
    if user_in.otp != "1234":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP.")

    hashed_password = bcrypt.hashpw(user_in.new_password.encode('utf-8'), bcrypt.gensalt())
    current_user.hashed_password = hashed_password

    await db.commit()
    return {"status": "Success"}


@router.post('/set_profile')
async def set_profile(user_in: UserSetProfile, current_user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db_session)):
    user = await db.execute(select(User).where(User.number == user_in.number))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found.")

    user_with_same_username = await db.execute(select(User).where(User.username == user_in.username))
    if user_with_same_username.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")

    current_user.username = user_in.username
    current_user.name = user_in.name

    await db.commit()
    return {"status": "Success"}


@router.post('/forget_password', status_code=status.HTTP_202_ACCEPTED)
async def forget_password(user_in: UserForgetPassword, db: AsyncSession = Depends(get_db_session)):
    user = await db.execute(select(User).where(User.number == user_in.number))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found.")

    hashed_password = bcrypt.hashpw(user_in.new_password.encode('utf-8'), bcrypt.gensalt())
    user.hashed_password = hashed_password

    await db.commit()
    return {"status": "Success"}
