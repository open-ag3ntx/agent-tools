import os
from base.settings import settings
from base.models import BaseToolResult
from base.file_utils import get_file_type, write_file_content
from typing import Annotated, Optional

class WriteFileResult(BaseToolResult):
    new_file_created: bool = False


async def write_file(
    file_path: Annotated[str, "The absolute path to the file to write/create"],
    content: Annotated[str, "The content to write to the file"],
    ) -> WriteFileResult:
    """
    Writes a file to the local filesystem.
    Usage:
    - This tool will overwrite the existing file if there is one at the provided path.
    - If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
    - Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.
    """
    try:
        # Security check: ensure file is within allowed directories
        if not file_path.startswith(settings.present_working_directory) and not file_path.startswith("/tmp/"):
            return WriteFileResult(success=False, error="File is not allowed to be written outside the present working directory")
        
        new_file_created = False
        
        if os.path.exists(file_path):
            # File exists - check if it's actually a file and writable
            if not os.path.isfile(file_path):
                return WriteFileResult(success=False, error="Path is a directory, not a file")
            if not os.access(file_path, os.W_OK):
                return WriteFileResult(success=False, error="File is not writable")
            
            # Check if existing file is a text file
            file_type = await get_file_type(file_path)
            if file_type != "text":
                return WriteFileResult(success=False, error="File is not a text file")
        else:
            # File doesn't exist - check if parent directory exists and is writable
            parent_dir = os.path.dirname(file_path)
            if not parent_dir:
                parent_dir = "."
            
            if not os.path.exists(parent_dir):
                return WriteFileResult(success=False, error="Parent directory does not exist")
            if not os.path.isdir(parent_dir):
                return WriteFileResult(success=False, error="Parent path is not a directory")
            if not os.access(parent_dir, os.W_OK):
                return WriteFileResult(success=False, error="Parent directory is not writable")
            
            new_file_created = True
        
        await write_file_content(file_path, content)

        if new_file_created:
            return WriteFileResult(success=True, content=f"File {file_path} has been created successfully", new_file_created=True)
        else:
            return WriteFileResult(success=True, content=f"File {file_path} has been written successfully", new_file_created=False)

    except Exception as e:
        return WriteFileResult(success=False, error=f"Error writing file: {e}")


def display_write_file(
    file_path: str,
    content: str,
    ) -> str:
    """Generates a human-readable summary of the write_file action."""
    return f'Write File {file_path}'