from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import datetime, timedelta

# from models.todo_model import Todo
from models.user_model import User, UserProfile
from config.db import todo_collection, users_collection

from bson import ObjectId
from typing import List, Annotated

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
SECRET_KEY = f"""{os.getenv("TODOAPP_SECRET_KEY")}"""  # Generate Secret Key with `openssl rand -hex 32`
ALGORITHM = f"""{os.getenv("TODOAPP_ALGORITHM")}"""
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("TODOAPP_ACCESS_TOKEN_EXPIRE_MINUTES"))

ERROR_CONNECTION_VALIDATION = "Could not validate connection."

user_router = APIRouter(
    prefix="/api/v1/user",
    tags=["users"],
)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/user/token")


class CreateUserRequest(BaseModel):
    email: str
    password: str
    profile: UserProfile


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


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """
    x
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
    # if not verify_password(password, user.hashed_password):
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


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
            profile=create_user_request.profile,
        )
        # users_collection.insert_one(dict(create_user_model))
        users_collection.insert_one(create_user_model.model_dump())


@user_router.post("/token")
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


@user_router.get("/profile/")
async def get_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """
    x
    """
    return current_user
