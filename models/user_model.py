from pydantic import BaseModel, Field
# from typing import List


class UserProfile(BaseModel):
    name: str
    pfp: str  # TODO change to base64 later


class User(BaseModel):
    email: str
    password: str
    user_id: str | None = None
    # active_sessions: List[str] | None = []
    refresh_token: str | None = None
