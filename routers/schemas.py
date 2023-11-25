from pydantic import BaseModel
from typing import Optional


class UserIn(BaseModel):
    number: str
    otp_or_password: str


class UserVerifyPassword(BaseModel):
    number: str
    password: str


class UserSetPassword(BaseModel):
    number: str
    new_password: str
    otp: str


class UserSetProfile(BaseModel):
    number: str
    password: str
    username: str
    name: str


class UserForgetPassword(BaseModel):
    number: str
