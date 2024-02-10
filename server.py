from rich import print

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from auth import auth_router

from routes.todo_routes import todo_router
from routes.user_routes import user_router
from routes.jinja_routes import jinja_router

from middleware.logger import log_middleware, logger


# Define our app and add any relevant middleware
app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)

# Set the StaticFiles location for our assets (like CSS)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Add our routes
routers = [
    auth_router,
    user_router,
    todo_router,
    jinja_router,
]

for router in routers:
    app.include_router(router=router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"hello": "world"}

# Start the server with uvicorn
if __name__ == "__main__":
    import uvicorn
    # print("[green]STARTING UP...![/green]")
    logger.info("Starting up!")
    uvicorn.run("server:app", host="0.0.0.0", port=8181, reload=True)
