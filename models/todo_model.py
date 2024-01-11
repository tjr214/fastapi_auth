from pydantic import BaseModel, Field


class Todo(BaseModel):
    name: str
    description: str
    task_complete: bool
    owner_id: str
