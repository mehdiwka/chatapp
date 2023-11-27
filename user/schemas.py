import datetime

from pydantic import BaseModel, field_validator
from typing import Optional


class UserBase(BaseModel):
    number: str

    @field_validator("number")
    def validate_iran_phone_number(cls, values):
        number = values
        if number and len(number) == 11 and number.isdigit():
            return values
        raise ValueError('Invalid phone number')


class Register(UserBase):
    otp: str = None


class Login(UserBase):
    otp: str = None
    password: str


class UserVerifyPassword(UserBase):
    password: str


class UserSetPassword(UserBase):
    new_password: str


class UserSetProfile(UserBase):
    password: str
    username: str
    name: str


class UserForgetPassword(UserBase):
    pass
class SessionBase(BaseModel):
    id: int
    user_id: int
    device_info: Optional[str]
    session_token: str
    created_at: Optional[datetime.datetime]

    class Config:
        orm_mode = True
