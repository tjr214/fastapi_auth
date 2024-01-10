from pydantic import BaseModel, Field


class Todo(BaseModel):
    # id: str = Field(None, alias='_id')
    name: str
    description: str
    task_complete: bool
