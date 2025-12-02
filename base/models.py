from pydantic import BaseModel
from typing import Optional
from typing import Literal


class CommandResult(BaseModel):
    success: bool = True
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    command: Optional[str] = None
    working_directory: Optional[str] = None
    timed_out: bool = False

class BaseToolResult(BaseModel):
    success: bool = True
    error: Optional[str] = None
    content: Optional[str] = None

class TodoItem(BaseModel):
    id: int
    task_group: str
    title: str
    status: Literal["pending", "completed", "cancelled"] = "pending"


