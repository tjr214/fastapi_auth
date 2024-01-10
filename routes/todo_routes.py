# from rich import print
from fastapi import APIRouter, status

from models.todo_model import Todo
from config.db import todo_collection, users_collection
from bson import ObjectId
from typing import List

todo_router = APIRouter(
    prefix="/api/v1/todo",
    tags=["todos"],
)


@todo_router.get("/", status_code=status.HTTP_200_OK)
async def get_todos() -> List[dict]:
    return_list = []
    for todo_data in todo_collection.find():
        todo = {
            "id": str(todo_data["_id"]),
            "name": todo_data["name"],
            "description": todo_data["description"],
            "task_complete": todo_data["task_complete"],
        }
        return_list.append(todo)
    return return_list


@todo_router.post("/", status_code=status.HTTP_201_CREATED)
def post_todo(todo: Todo):
    # Notice: NO ASYNC because writing to dB
    todo_collection.insert_one(dict(todo))
    return {
        "status": 1,
        "data": "insert_good",
    }


@todo_router.put("/{id}", status_code=status.HTTP_200_OK)
def update_todo(id: str, todo: Todo):
    # Notice: NO ASYNC because writing to dB
    todo_collection.find_one_and_update(
        {"_id": ObjectId(id)}, {"$set": dict(todo)})


@todo_router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_todo(id: str):
    # Notice: NO ASYNC because writing to dB
    todo_collection.find_one_and_delete({"_id": ObjectId(id)})
