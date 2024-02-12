from pydantic import BaseModel, Field
# from typing import List


class UserProfile(BaseModel):
    name: str
    pfp: str  # TODO change to base64 later


class User(BaseModel):
    email: str
    password: str
    user_id: str | None = None
    refresh_token: str | None = None
    # active_session_tokens: List[str] | None = []
    # active_refresh_tokens: List[str] | None = []
    # admin : bool | None = False
