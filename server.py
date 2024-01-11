from rich import print

from fastapi import FastAPI, status, HTTPException

from routes.todo_routes import todo_router
from routes.user_routes import user_router
from util.auth import auth_router

from models.user_model import User

app = FastAPI()

routers = [
    user_router,
    todo_router,
    auth_router,
]

# Add our routes:
for router in routers:
    app.include_router(router=router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"hello": "world"}

# Start the server with uvicorn
if __name__ == "__main__":
    import uvicorn
    print("[green]STARTING UP...![/green]")
    uvicorn.run("server:app", host="0.0.0.0", port=8181, reload=True)
