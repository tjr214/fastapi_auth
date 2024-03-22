from typing import Annotated
from bson import ObjectId
from datetime import timedelta

from fastapi import APIRouter, Response, Request, Depends, HTTPException, status
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from backend.config.constants import (
    FRONTEND_PAGE_TEMPLATES,
)

from backend.config.db import users_collection
from backend.models.user_model import User, UserProfile

from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    GITHUB_CLIENT_ID,
    GITHUB_SECRET_KEY,
    Token,
    get_confirmed_user,
    create_access_token,
    verify_access_token,
    credential_exception
)

from backend.auth import (
    get_password_hash,
    get_user_from_db,
    get_user_from_token,
    get_user_from_cookie,
)


import httpx
from dotenv import load_dotenv

from backend.config.db import users_collection
from backend.log import get_logger


# Get our good 'ol Logger
logger = get_logger(__name__)

# Load environment variables from the .env file
load_dotenv()


user_router = APIRouter(
    # prefix=f"{API_PREFIX}/user",
    prefix="/user",
    tags=["User-related stuff"],
)

templates = Jinja2Templates(directory=FRONTEND_PAGE_TEMPLATES)


# Github OAuth variables:
github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
github_token_url = "https://github.com/login/oauth/access_token"


class CreateUserRequest(BaseModel):
    email: str
    password: str


# ------------------------------------------------------------------------
# GET SECTION (redirect to frontend)
# ------------------------------------------------------------------------
@user_router.get("/")
async def get_index(request: Request, active_user: User = Depends(get_user_from_cookie)):
    if not active_user:
        return RedirectResponse("/user/login", status_code=status.HTTP_302_FOUND)
    # return templates.TemplateResponse(f"/static/test.html", {"request": request})


@user_router.get("/profile")
async def get_user_profile(request: Request, active_user: User = Depends(get_user_from_cookie)) -> User:
    """
    Returns a `User` object representing the current_user.
    """
    if not active_user:
        return RedirectResponse("/user/login", status_code=status.HTTP_302_FOUND)
    return active_user


@user_router.get("/register")
async def get_signup(request: Request):
    return templates.TemplateResponse(f"/register.html", {"request": request})


@user_router.get("/login")
async def email_login(request: Request):
    return templates.TemplateResponse(f"/login.html", {"request": request, "appname": "Roger-Roger"})


@user_router.get("/login/github")
async def github_login():
    """
    x
    """
    # might also use: status.HTTP_307_TEMPORARY_REDIRECT
    logger.info(f"GITHUB OAUTH REDIRECT: {github_auth_url}")
    return RedirectResponse(github_auth_url, status_code=status.HTTP_302_FOUND)


@user_router.get("/oauth/get-github-code")
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

    access_token = None
    if "access_token" in response:
        access_token = response["access_token"]
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

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


# ------------------------------------------------------------------------
# POST SECTION (API functions)
# ------------------------------------------------------------------------

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user(create_user_request: CreateUserRequest):
    """
    Create a new user in the dB.
    """
    if get_user_from_db(create_user_request.email):
        # Email is already registered
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Email address already registered: {create_user_request.email}",
        )
    else:
        create_user_model = User(
            email=create_user_request.email,
            password=get_password_hash(create_user_request.password),
        )
        users_collection.insert_one(create_user_model.model_dump())


@user_router.post("/login")
async def login_for_access_token(response: Response, request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    This is the login route for tokens (email/password login).
    It retrieves an `authenticated_user()` with the form's username and password,
    gets the associated user ID from the db and patches it in to the object,
    generates access & refresh tokens, adds the refresh token to the db and returns the access token.
    """
    user = get_confirmed_user(form_data.username, form_data.password)

    if not user:
        error = "Could not validate connection."
        logger.info("Invalid Login Request.")
        return templates.TemplateResponse(f"/login.html", {"error": error, "username": form_data.username, "password": form_data.password, "request": request}, status_code=status.HTTP_401_UNAUTHORIZED)

    user_id = users_collection.find_one({"email": user.email})["_id"]
    access_token = create_access_token(
        email=user.email,
        id=str(user_id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_access_token(
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

    # Save our Access Token in a cookie
    response.set_cookie(
        key="rr-access-token",
        # value=f"Bearer {access_token}",
        value=f"{access_token}",
        httponly=True
    )

    # Now save the Refresh Token in a cookie
    response.set_cookie(
        key="rr-refresh-token",
        # value=f"Bearer {refresh_token}",
        value=f"{refresh_token}",
        # max_age=x,
        httponly=True
    )

    return response


@user_router.post("/refresh_token", status_code=status.HTTP_200_OK)
# async def renew_access_tokens(refresh_token: Annotated[str, Depends(oauth2_bearer)]):
async def renew_access_tokens(refresh_token: str):
    """
    If the `refresh_token` is still valid, gen a new access token for our user.
    Else, error out.
    """
    token_data = verify_access_token(refresh_token)
    if token_data:
        # Refresh token is valid and we need to return a new access token.
        access_token = create_access_token(
            email=token_data["username"],
            id=str(token_data["id"]),
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        print(
            f"[yellow]\[{token_data['username']}] Token Refresh: requested and granted![/yellow]")
        logger.info(
            f"[{token_data['username']}] Token Refresh: requested and granted!")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }
    else:
        # Refresh token is NOT valid and we need to raise an error.
        print(
            "[red]Attempted request for token refresh, but Refresh Token is INVALID![/red]")
        logger.info(
            "Attempted request for token refresh, but Refresh Token is INVALID!")
        raise credential_exception
