from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str
    pfp: str  # TODO change to base64 later


class User(BaseModel):
    email: str
    hashed_password: str
    user_id: str
