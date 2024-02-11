import os
from typing import Annotated
from bson import ObjectId
from datetime import datetime, timedelta
# import uuid

from fastapi import APIRouter, Response, Request, Depends, HTTPException, status
from starlette.responses import RedirectResponse
from backend.auth_cookie import OAuth2PasswordBearerWithCookie
from fastapi.security import OAuth2PasswordRequestForm  # , OAuth2PasswordBearer


from pydantic import BaseModel
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
import httpx

from dotenv import load_dotenv

from backend.models.user_model import User
from backend.config.db import users_collection
from backend.config.constants import API_PREFIX, ERROR_CONNECTION_VALIDATION

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

# Some Github OAuth variables:
github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
github_token_url = "https://github.com/login/oauth/access_token"


auth_router = APIRouter(
    prefix=f"{API_PREFIX}/auth",
    tags=["auth"],
)

# Hashing context
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use our special cookie-enabled OAuth2 bearers
oauth2_bearer = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{API_PREFIX}/auth/token")
github_oauth_bearer = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{API_PREFIX}/auth/github-code")

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=ERROR_CONNECTION_VALIDATION,
    headers={"WWW-Authenticate": "Bearer"}
)


class Token(BaseModel):
    access_token: str
    token_type: str


def verify_access_token(token: Annotated[str, Depends(oauth2_bearer)] | Annotated[str, Depends(github_oauth_bearer)]) -> dict | None:
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

        # print(
        #     f"[yellow]\[{email}] Time till token expiration:[/yellow]", check_date)

        logger.info(
            f"[{email}] Time till token expiration: {check_date}")

        if email is None or user_id is None:
            raise credential_exception
        token_data = {"username": email, "id": user_id}
    except ExpiredSignatureError:
        print("[red]ExpiredSignatureERROR![/red]")
        return None
    except JWTError:
        print("[red]BRO ALERT: [i]Bad Token Detected & Rejected, bruh.[/i][/red]")
        raise credential_exception
    return token_data


def create_jwt_token(email: str, id: str, expires_delta: timedelta) -> str:
    """
    Create a JWT token for access or refresh.
    """
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(claims=encode, key=SECRET_KEY, algorithm=ALGORITHM)


def get_user(email: str, **kwargs) -> User | None:
    """
    Uses the user's email address to find the account and return a `User` object.
    If there is an `id` in the kwargs, assign it to the returned user.
    """
    for user_data in users_collection.find():
        if user_data["email"] == email:
            # instead of using kwargs, we should just be able to do:
            # user_data["user_id"] = user_data["_id"]
            if "id" in kwargs:
                user_data["user_id"] = kwargs["id"]
            return User(**user_data)


async def get_authenticated_user(token: Annotated[str, Depends(oauth2_bearer)] | Annotated[str, Depends(github_oauth_bearer)]) -> User | None:
    """
    Return a `User` object representing the active user, validated via an access token.
    """
    token_data = verify_access_token(token=token)
    if not token_data:
        raise credential_exception
    user = get_user(email=token_data["username"], id=token_data["id"])
    if user is None:
        raise credential_exception
    return user


def authenticate_user(email: str, password: str) -> User:
    """
    Authenticate by verifying the password is the same as the hashed_password in the db.
    """
    user = get_user(email=email)
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user


@auth_router.post("/token")
async def login_for_access_token(response: Response, request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    This is the login route for tokens (email/password login).
    It retrieves an `authenticated_user()` with the form's username and password,
    gets the associated user ID from the db and patches it in to the object,
    generates access & refresh tokens, adds the refresh token to the db and returns the access token.
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        error = "No good login."
        raise credential_exception
        # return templates.TemplateResponse('auth/signin.html', {"error": error, "request": request}, status_code=301)

    user_id = users_collection.find_one({"email": user.email})["_id"]
    access_token = create_jwt_token(
        email=user.email,
        id=str(user_id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_jwt_token(
        email=user.email,
        id=str(user_id),
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    # session_id = uuid.uuid4()

    # # Add the `session_id` to the List of active_sessions
    # users_collection.find_one_and_update(
    #     {"_id": ObjectId(user_id)}, {"$push": {"active_sessions": str(session_id)}})

    users_collection.find_one_and_update(
        {"_id": ObjectId(user_id)}, {"$set": {"refresh_token": refresh_token}})

    response = RedirectResponse(
        url="/", status_code=status.HTTP_302_FOUND)

    # Now save the Token in a cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True
    )

    return response
    # return {
    #     "access_token": access_token,
    #     "token_type": "Bearer",
    #     # "session_id": session_id,
    # }


@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
# async def renew_access_tokens(refresh_token: Annotated[str, Depends(oauth2_bearer)]):
async def renew_access_tokens(refresh_token: str):
    """
    If the `refresh_token` is still valid, gen a new access token for our user.
    Else, error out.
    """
    token_data = verify_access_token(refresh_token)
    if token_data:
        # Refresh token is valid and we need to return a new access token.
        access_token = create_jwt_token(
            email=token_data["username"],
            id=str(token_data["id"]),
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        print(
            f"[yellow]\[{token_data['username']}] Token Refresh: requested and granted![/yellow]")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }
    else:
        # Refresh token is NOT valid and we need to raise an error.
        print(
            "[red]Attempted request for token refresh, but Refresh Token is INVALID![/red]")
        raise credential_exception


@auth_router.get("/github-login")
async def github_login():
    """
    x
    """
    # might also use: status.HTTP_307_TEMPORARY_REDIRECT
    logger.info(f"REDIRECT: {github_auth_url}")
    return RedirectResponse(github_auth_url, status_code=status.HTTP_302_FOUND)


@auth_router.get("/github-code")
async def github_code(code: str):
    """
    x
    """
    logger.info(f"GITHUB YIELDED CODE: {code}")
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_SECRET_KEY,
        "code": code,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url=github_token_url, params=params, headers=headers)
    response = response.json()
    logger.info(f"RESPONSE FROM GITHUB TOKEN URL: {response}")
    access_token = response["access_token"]
    token_data = {
        "access_token": access_token,
        "token_type": "Bearer",
    }
    async with httpx.AsyncClient() as client:
        headers.update({"Authorization": f"Bearer {access_token}"})
        response = await client.get(url="https://api.github.com/user", headers=headers)
    response = response.json()
    user_data = {}
    if not response["email"]:
        user_data["username"] = response["login"]
    else:
        user_data["username"] = response["email"]
    print(user_data)
    return token_data
