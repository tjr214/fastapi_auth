from fastapi import APIRouter, Depends, status

from backend.auth import get_confirmed_user, bcrypt_context

from backend.models.todo_model import Todo
from backend.models.user_model import User

from backend.config.db import content_collection
from backend.config.constants import API_PREFIX

from bson import ObjectId
from typing import List

todo_router = APIRouter(
    prefix=f"{API_PREFIX}/todo",
    tags=["todos"],
)


@todo_router.get("/", status_code=status.HTTP_200_OK)
async def get_todos(current_user: User = Depends(get_confirmed_user)) -> List[dict]:
    return_list = []
    for todo_data in content_collection.find():
        if todo_data["owner_id"] == current_user.user_id:
            todo = {
                "id": str(todo_data["_id"]),
                "name": todo_data["name"],
                "description": todo_data["description"],
                "task_complete": todo_data["task_complete"],
            }
            return_list.append(todo)
    return return_list


@todo_router.post("/", status_code=status.HTTP_201_CREATED)
def create_todo(todo: Todo, current_user: User = Depends(get_confirmed_user)):
    # Notice: NO ASYNC because writing to dB
    # Insert the new Item into the `content_collection`
    todo.owner_id = current_user.user_id
    content_collection.insert_one(todo.model_dump())


@todo_router.put("/{id}", status_code=status.HTTP_200_OK)
def update_todo(id: str, todo: Todo, current_user: User = Depends(get_confirmed_user)):
    # Notice: NO ASYNC because writing to dB
    todo.owner_id = current_user.user_id
    content_collection.find_one_and_update(
        {"_id": ObjectId(id)}, {"$set": todo.model_dump()})


@todo_router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_todo(id: str, current_user: User = Depends(get_confirmed_user)):
    # Notice: NO ASYNC because writing to dB
    content_collection.find_one_and_delete({"_id": ObjectId(id)})
