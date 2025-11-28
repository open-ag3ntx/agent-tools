from typing import Annotated
import os

from models import BaseToolResult

class ReadFileResult(BaseToolResult):
    content: str

FILE_SIZE_LIMIT = 10 * 1024 * 1024 # 100MB


def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    limit: Annotated[int, "The maximum number of lines to read"] = 2000,
    offset: Annotated[int, "The number of lines to skip"] = 0
) -> BaseToolResult:
    """"""
    try:
        if not os.path.exists(file_path):
            return ReadFileResult(
                success=False,
                error=(
                    "Could not read content of the file because it does not exist at the given path",
                )
            )
        if not os.path.isfile(file_path):
            return ReadFileResult(
                success=False,
                error=(
                    "Could not read content of the file because it is a directory, not a file",
                )
            )
        file_metadata = os.stat(file_path)
        if file_metadata.st_size > FILE_SIZE_LIMIT:
            return ReadFileResult(
                success=False,
                error=(
                    "Could not read content of the file because it is too large, the maximum size is 10MB",
                )
            )
        
    except Exception as e:
        return f"Error reading file: {e}"
    