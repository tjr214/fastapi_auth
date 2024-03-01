import os

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.routes.user_routes import user_router
from backend.routes.todo_routes import todo_router
from backend.routes.jinja_routes import jinja_router

from backend.log import get_logger
from backend.middleware.logger import log_route

from backend.config.constants import (
    FRONTEND_PAGE_TEMPLATES,
    FRONTEND_APP_PAGES
)

from dotenv import load_dotenv
load_dotenv()


# Get our initial logger
logger = get_logger(__name__)

# Define our app and add any relevant middleware
app = FastAPI(
    title="My New App",
    description="My New App is a super badass app that does badass things with stuff.",
    summary="TODO: Summary of the App goes here.",
    version="0.0.1"
)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_route)

# Set the StaticFiles location for our assets (like CSS and images, etc.)
app.mount(
    "/static", StaticFiles(directory="frontend/static", html=True),
    name="static-assets"
)

templates = Jinja2Templates(directory=FRONTEND_PAGE_TEMPLATES)

# Add our routes
routers = [
    user_router,
    todo_router,
    jinja_router,
]
for router in routers:
    app.include_router(router=router)


# Set the `favicon` for your App (if desired)
@app.get("/favicon.ico")
async def get_favicon():
    return RedirectResponse("/static/favicon.ico", status_code=status.HTTP_302_FOUND)


# Handle the root "homepage" for the App
@app.get("/", status_code=status.HTTP_200_OK)
async def root_index(request: Request):
    return templates.TemplateResponse(f"{FRONTEND_APP_PAGES}/home/index.html", {"request": request})


# Start the server with uvicorn
if __name__ == "__main__":
    SERVER_HOST = str(os.getenv("SERVER_HOST", "0.0.0.0"))
    SERVER_PORT = int(os.getenv("SERVER_PORT", 9393))
    SERVER_RELOAD = bool(os.getenv("SERVER_RELOAD", 0))
    import uvicorn
    import time
    time_start = time.time()
    logger.info("Starting up!")
    uvicorn.run(
        app="server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=SERVER_RELOAD
    )
    logger.info(f"SHUTTING DOWN; runtime: '{time.time() - time_start}s'")
