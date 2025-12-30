from langchain.messages import ToolMessage
from langchain_core.load import dumps
from langchain_core.runnables.schema import EventData
from rich.syntax import Syntax
from os import stat_result
from numbers import Number
from typing import Annotated, Optional, Literal
import os

from base.settings import settings
from base.file_utils import get_file_type, read_file_content, get_file_extension
from base.models import BaseToolResult, GlobToolResult

class ReadFileResult(BaseToolResult):
    content: Optional[str] = None

FILE_SIZE_LIMIT: Literal[10485760] = 10 * 1024 * 1024 # 100MB

MAX_LINES_TO_READ = 2000
MAX_LENGTH_OF_LINE = 2000

async def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    limit: Annotated[Optional[int], "The maximum number of lines to read"] = 2000,
    offset: Annotated[Optional[int], "The number of lines to skip"] = 0
) -> str:
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
            ).model_dump_json()
        if not os.path.isfile(file_path):
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is a directory, not a file"
            ).model_dump_json()
        if not file_path.startswith(settings.present_working_directory) and not file_path.startswith("/tmp/"):
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is not allowed to read files outside the present working directory"
            ).model_dump_json()
        file_metadata: stat_result = os.stat(file_path)
        if file_metadata.st_size > FILE_SIZE_LIMIT:
            return ReadFileResult(
                success=False,
                error="Could not read content of the file because it is too large, the maximum size is 10MB"
            ).model_dump_json()
        
        file_type: str = await get_file_type(file_path)
        if file_type != "text":
            return ReadFileResult(
                success=False,
                error="This file doesnt seem to be having text content, only files having text content can be read"
            ).model_dump_json()
        
        file_content: str = await read_file_content(file_path)
        if len(file_content) == 0:
            return ReadFileResult(
                success=True,
                content="This file is empty"
            ).model_dump_json()
        lines: list[str] = file_content.split("\n")
        start_line = max(0, min(offset, len(lines) - 1))
        end_line: int = min(start_line + limit, len(lines))
        selected_lines: list[str] = lines[start_line:end_line]

        # truncate the lines to the maximum length of line but add ... to the end if it is truncated
        # add line numbers to the lines The line number prefix format is: spaces + line number + tab
        selected_lines = [
            f" {i+1}\t{line[:MAX_LENGTH_OF_LINE] + '... truncated' if len(line) > MAX_LENGTH_OF_LINE else line}"
            for i, line in enumerate(selected_lines)
        ]

        return ReadFileResult(
            success=True, content="\n".join(selected_lines)
        ).model_dump_json()

    except Exception as e:
        return ReadFileResult(
            success=False,
            error=f"Error reading file: {e}"
        ).model_dump_json()
    
def display_read_file(file_path: str, limit: Optional[int] = None, offset: Optional[int] = None) -> str:
    """Generates a human-readable summary of the read_file action."""
    if limit is not None and offset is not None:
        return f'Reading File {file_path}:{offset + 1}:{offset + limit}'
    else:
        return f'Reading File {file_path}'

def get_read_file_tool_output(data: EventData) -> Syntax:
    output = data['output']
    if isinstance(output, ToolMessage):
        content = output.content
    elif isinstance(output, dict):
        content = output.get('content')
    else:
        content = None

    if content is None:
        syntax = Syntax(
            "Error: No content returned from read_file tool.",
            "text",
            theme="ansi_dark",
            line_numbers=False
        )
        return syntax
    result: ReadFileResult = ReadFileResult.model_validate_json(content)
    if result.success and result.content:
        file_path = data.get('input', {}).get('file_path') or data.get('input', {}).get('path', 'python')
        file_type = get_file_extension(file_path)
        syntax = Syntax(
            result.content,
            file_type,
            theme="ansi_dark",
            line_numbers=False
        )
        return syntax
    return Syntax(
        f"Error reading file: {result.error}",
        "text",
        theme="ansi_dark",
        line_numbers=False
    )
