from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Annotated

from auth import get_user, get_authenticated_user, bcrypt_context

from models.user_model import User, UserProfile

from config.db import users_collection
from config.constants import API_PREFIX


user_router = APIRouter(
    prefix=f"{API_PREFIX}/user",
    tags=["users"],
)


class CreateUserRequest(BaseModel):
    email: str
    password: str
    # profile: UserProfile


@user_router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(create_user_request: CreateUserRequest):
    """
    x
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
            hashed_password=bcrypt_context.hash(create_user_request.password),
            user_id="0",
        )
        # users_collection.insert_one(dict(create_user_model))
        users_collection.insert_one(create_user_model.model_dump())


@user_router.get("/profile/")
async def get_user_profile(current_user: User = Depends(get_authenticated_user)) -> User:
    """
    x
    """
    return current_user
