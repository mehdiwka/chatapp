from pydantic import BaseModel


class UserIn(BaseModel):
    number: str
    username: str
    name: str
