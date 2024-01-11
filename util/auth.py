from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import datetime, timedelta

from models.user_model import User
from config.db import users_collection
from config.constants import API_PREFIX, ERROR_CONNECTION_VALIDATION

# from util.user_utils import get_user

from typing import Annotated

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
SECRET_KEY = f"""{os.getenv("TODOAPP_SECRET_KEY")}"""  # Generate Secret Key with `openssl rand -hex 32`
ALGORITHM = f"""{os.getenv("TODOAPP_ALGORITHM")}"""
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("TODOAPP_ACCESS_TOKEN_EXPIRE_MINUTES"))


auth_router = APIRouter(
    prefix=f"{API_PREFIX}/auth",
    tags=["users"],
)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(email: str, id: str, expires_delta: timedelta) -> str:
    """
    Create a JWT access token
    """
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(claims=encode, key=SECRET_KEY, algorithm=ALGORITHM)


def get_user(email: str) -> User | None:
    """
    Uses the user's email address to find the account and return a `User` object
    """
    for user_data in users_collection.find():
        if user_data["email"] == email:
            return User(**user_data)


async def get_authenticated_user(token: Annotated[str, Depends(oauth2_bearer)]) -> User:
    """
    Return a `User` object representing the active user, validated via an access token
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_CONNECTION_VALIDATION,
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        email: str = payload.get("sub")
        user_id: str = payload.get("id")
        if email is None or user_id is None:
            raise credential_exception
        token_data = {"username": email, "id": user_id}
    except JWTError:
        raise credential_exception

    user = get_user(email=token_data["username"])
    if user is None:
        raise credential_exception
    return user


def authenticate_user(email: str, password: str) -> User:
    """
    Authenticate by verifying the password is the same as the hashed_password in the db
    """
    user = get_user(email=email)
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


@auth_router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_CONNECTION_VALIDATION,
            headers={"WWW-Authenticate": "Bearer"}
        )
    user_id = users_collection.find_one({"email": user.email})["_id"]
    access_token = create_access_token(
        email=user.email,
        id=str(user_id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
