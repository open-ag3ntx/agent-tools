from pydantic import BaseModel
from typing import Optional


class CommandResult(BaseModel):
    success: bool = True
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    command: Optional[str] = None
    working_directory: Optional[str] = None
    timed_out: bool = False

