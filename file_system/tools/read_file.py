from typing import Annotated, Optional
import os

from base.settings import settings
from base.utils import get_file_type, read_file_content
from base.models import BaseToolResult

class ReadFileResult(BaseToolResult):
    content: Optional[str] = None

FILE_SIZE_LIMIT = 10 * 1024 * 1024 # 100MB

MAX_LINES_TO_READ = 2000
MAX_LENGTH_OF_LINE = 2000

async def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    limit: Annotated[Optional[int], "The maximum number of lines to read"] = 2000,
    offset: Annotated[Optional[int], "The number of lines to skip"] = 0
) -> BaseToolResult:
    """
    Reads a file from the local filesystem. You can access any file directly by using this tool.Assume this tool is able to read all files on the machine. 
    If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.
    Usage:
    - The file_path parameter must be an absolute path, not a relative path
    - By default, it reads up to 2000 lines starting from the beginning of the file
    - You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
    - Any lines longer than 2000 characters will be truncated
    - Results are returned using cat -n format, with line numbers starting at 1
    - This tool can only read files, not directories.
    - You can call multiple tools in a single response. It is always better to speculatively read multiple potentially useful files in parallel.
    - If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.
    """
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
        if len(file_content) == 0:
            return ReadFileResult(
                success=True,
                content="This file is empty"
            )
        lines = file_content.split("\n")
        start_line = max(0, min(offset, len(lines) - 1))
        end_line = min(start_line + limit, len(lines))
        selected_lines = lines[start_line:end_line]

        # truncate the lines to the maximum length of line but add ... to the end if it is truncated
        # add line numbers to the lines The line number prefix format is: spaces + line number + tab
        selected_lines = [
            f" {i+1}\t{line[:MAX_LENGTH_OF_LINE] + '... truncated' if len(line) > MAX_LENGTH_OF_LINE else line}"
            for i, line in enumerate(selected_lines)
        ]

        return ReadFileResult(
            success=True, content="\n".join(selected_lines)
        )

    except Exception as e:
        return ReadFileResult(
            success=False,
            error=f"Error reading file: {e}"
        )
    