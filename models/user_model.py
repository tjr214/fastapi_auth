from pydantic import BaseModel, Field
from typing import List

from .todo_model import Todo


class UserProfile(BaseModel):
    name: str
    pfp: str  # TODO change to base64 later


class User(BaseModel):
    email: str
    hashed_password: str
    profile: UserProfile
    todos: List[Todo] = []
