from rich import print

from fastapi import FastAPI, status, HTTPException
from fastapi.staticfiles import StaticFiles


from routes.todo_routes import todo_router
from routes.user_routes import user_router
from routes.jinja_routes import jinja_router
from auth import auth_router


app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


routers = [
    auth_router,
    user_router,
    todo_router,
    jinja_router,
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
