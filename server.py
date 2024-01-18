from rich import print

from fastapi import FastAPI, status, HTTPException
from fastapi.staticfiles import StaticFiles


from routes.todo_routes import todo_router
from routes.user_routes import user_router
from routes.jinja_routes import jinja_router
from auth import auth_router

# Define our app
app = FastAPI()

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
    print("[green]STARTING UP...![/green]")
    uvicorn.run("server:app", host="0.0.0.0", port=8181, reload=True)
