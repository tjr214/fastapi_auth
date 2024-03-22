import os
from typing import Annotated
from datetime import datetime, timedelta
# import uuid

from fastapi import APIRouter, Response, Request, Depends, HTTPException, status
from starlette.responses import RedirectResponse
from backend.auth_cookie import OAuth2PasswordBearerWithCookie
# from fastapi.security import OAuth2PasswordBearer

from pydantic import BaseModel
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from dotenv import load_dotenv

from backend.models.user_model import User
from backend.config.db import users_collection
from backend.config.constants import ERROR_CONNECTION_VALIDATION

from backend.log import get_logger
logger = get_logger(__name__)

# Load environment variables from the .env file
load_dotenv()

# Access environment variables for Token Auth:
SECRET_KEY = f"""{os.getenv("BACKEND_SECRET_KEY")}"""
ALGORITHM = f"""{os.getenv("BACKEND_ALGORITHM")}"""
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("BACKEND_REFRESH_TOKEN_EXPIRE_DAYS"))

# Access environment variables for Github OAuth:
GITHUB_CLIENT_ID = f"""{os.getenv("GITHUB_CLIENT_ID")}"""
GITHUB_SECRET_KEY = f"""{os.getenv("GITHUB_SECRET_KEY")}"""

# Hashing context
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use our special cookie-enabled OAuth2 bearers
oauth_bearer = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"user/login")
github_oauth_bearer = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"user/oauth/get-github-code")

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=ERROR_CONNECTION_VALIDATION,
    headers={"WWW-Authenticate": "Bearer"}
)


class Token(BaseModel):
    access_token: str
    token_type: str


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def verify_access_token(token: Annotated[str, Depends(oauth_bearer)] | Annotated[str, Depends(github_oauth_bearer)]) -> dict | None:
    """
    Verify the token is a good token and has not expired or gotten itself involved in
    anything nefarious by associating with data of ill repute.
    """
    try:
        payload = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        email: str = payload.get("sub")
        user_id: str = payload.get("id")
        exp: timedelta = payload.get("exp")
        exp = datetime.utcfromtimestamp(exp)
        check_date = exp - datetime.utcnow()

        logger.warning(
            f"[{email}] Time till token expiration: {check_date}")

        if email is None or user_id is None:
            raise credential_exception
        token_data = {"username": email, "id": user_id}
    except ExpiredSignatureError:
        logger.warning("ExpiredSignature: Token has expired!")
        return None
    except JWTError:
        logger.warning("JWTError: Bad Token detected & rejected!")
        # raise credential_exception
        return None
    return token_data


def create_access_token(email: str, id: str, expires_delta: timedelta) -> str:
    """
    Create a JWT token for access or refresh.
    """
    encode = {"sub": email, "id": id}
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encode.update({"exp": expires})
    return jwt.encode(claims=encode, key=SECRET_KEY, algorithm=ALGORITHM)


def get_user_from_db(email: str, **kwargs) -> User | None:
    """
    Uses the user's email address to find the account in the database and return a `User` object.
    If there is an `id` in the kwargs, assign it to the returned user.
    """
    for user_data in users_collection.find():
        if user_data["email"] == email:
            # instead of using kwargs, we should just be able to do:
            # user_data["user_id"] = user_data["_id"]
            if "id" in kwargs:
                user_data["user_id"] = kwargs["id"]
            return User(**user_data)


def get_confirmed_user(email: str, password: str) -> User:
    """
    Returns a "confirmed" `User` object , meaning: the user (`email`) exists
    in the database and the `password` is the correct password.
    """
    user = get_user_from_db(email=email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_user_from_token(token: Annotated[str, Depends(oauth_bearer)] | Annotated[str, Depends(github_oauth_bearer)]) -> User | None:
    """
    Return a `User` object representing the active `User`, validated via an access token.
    """
    token_data = verify_access_token(token=token)
    if not token_data:
        # raise credential_exception
        return None
    user = get_user_from_db(email=token_data["username"], id=token_data["id"])
    if user is None:
        # raise credential_exception
        return None
    return user


async def get_admin_from_token(token: Annotated[str, Depends(oauth_bearer)] | Annotated[str, Depends(github_oauth_bearer)]) -> User | None:
    """
    Return a `User` object representing the active Admin-enabled `User`, validated via an access token.
    """
    token_data = verify_access_token(token=token)
    if not token_data:
        raise credential_exception
    user = get_user_from_db(email=token_data["username"], id=token_data["id"])
    if user and user.admin:  # If getting errors, remember: UPDATE USER MODEL to add bool `admin` and nuke db!!!
        return user
    else:
        raise credential_exception


async def get_user_from_cookie(request: Request) -> User | None:
    """
    Return a `User` object representing the active `User`, validated via an access token encoded as a JWT.
    """
    cookie_value = request.cookies.get("rr-access-token")
    if not cookie_value:
        logger.warning("Unauthorized Access Attempted")
        return None
    else:
        # print(f"Good Cookie! {cookie_value}")
        return await get_user_from_token(token=cookie_value)
