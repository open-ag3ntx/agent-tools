from typing import Annotated, Optional
import os

from file_system.settings import settings
from file_system.utils import get_file_type, read_file_content
from file_system.models import BaseToolResult

class ReadFileResult(BaseToolResult):
    content: Optional[str] = None

FILE_SIZE_LIMIT = 10 * 1024 * 1024 # 100MB

MAX_LINES_TO_READ = 2000
MAX_LENGTH_OF_LINE = 2000

async def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    limit: Annotated[int, "The maximum number of lines to read"] = 2000,
    offset: Annotated[int, "The number of lines to skip"] = 0
) -> BaseToolResult:
    """"""
    try:
        if not os.path.exists(file_path):
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it does not exist at the given path"
            )
        if not os.path.isfile(file_path):
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is a directory, not a file"
            )
        if not file_path.startswith(settings.present_working_directory) and not file_path.startswith("/tmp/"):
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is not allowed to read files outside the present working directory"
            )
        file_metadata = os.stat(file_path)
        if file_metadata.st_size > FILE_SIZE_LIMIT:
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is too large, the maximum size is 10MB"
            )
        
        file_type = await get_file_type(file_path)
        if file_type != "text":
            return ReadFileResult(
                success=False,
                error="This file doesnt seem to be having text content, only files having text content can be read"
            )
        
        file_content = await read_file_content(file_path)
        lines = file_content.split("\n")
        start_line = max(0, min(offset, len(lines) - 1))
        end_line = min(start_line + limit, len(lines))
        selected_lines = lines[start_line:end_line]

        # truncate the lines to the maximum length of line but add ... to the end if it is truncated
        selected_lines = [
                line[:MAX_LENGTH_OF_LINE] + "... truncated" 
                if len(line) > MAX_LENGTH_OF_LINE else line 
                for line in selected_lines
            ]

        return ReadFileResult(
            success=True, content="\n".join(selected_lines)
        )

    except Exception as e:
        return ReadFileResult(
            success=False,
            error=f"Error reading file: {e}"
        )
    