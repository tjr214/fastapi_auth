from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
# from typing import List, Annotated

from backend.auth import get_user, get_authenticated_user, bcrypt_context

from backend.models.user_model import User, UserProfile

from backend.config.db import users_collection
from backend.config.constants import API_PREFIX


user_router = APIRouter(
    prefix=f"{API_PREFIX}/user",
    tags=["users"],
)


class CreateUserRequest(BaseModel):
    email: str
    password: str


@user_router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(create_user_request: CreateUserRequest):
    """
    Create a new user in the dB.
    """
    if get_user(create_user_request.email):
        # Email is already registered
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Email address already registered: {create_user_request.email}",
        )
    else:
        create_user_model = User(
            email=create_user_request.email,
            password=bcrypt_context.hash(create_user_request.password),
        )
        users_collection.insert_one(create_user_model.model_dump())


@user_router.get("/me/")
async def get_user_profile(current_user: User = Depends(get_authenticated_user)) -> User:
    """
    Returns a `User` object representing the current_user.
    """
    return current_user
