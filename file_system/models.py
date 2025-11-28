from pydantic import BaseModel
from typing import Optional

class BaseToolResult(BaseModel):
    success: bool = True
    error: Optional[str] = None