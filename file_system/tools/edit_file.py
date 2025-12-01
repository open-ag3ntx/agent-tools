import os
from file_system.settings import settings
from file_system.models import BaseToolResult
from file_system.utils import get_file_type, normalize_newlines, read_file_content, safe_replace, write_file_content
from typing import Annotated, Optional

class EditFileResult(BaseToolResult):
    new_file_created: bool = False


async def edit_file(
    file_path: Annotated[str, "The absolute path to the file to edit"],
    old_content: Annotated[str, "The content to replace in the file must be different from the new content"],
    new_content: Annotated[str, "The content to replace the old content with"],
    replace_all: Annotated[bool, "Replace all occurrences of the old content, if False, only the first occurrence will be replaced"] = False,
    ) -> EditFileResult:
    """
    Edit a file by replacing the old content with the new content.
    """
    try:
        if not os.path.exists(file_path):
            return EditFileResult(success=False, error="File does not exist")
        if not os.path.isfile(file_path):
            return EditFileResult(success=False, error="Path is not a file")
        if not file_path.startswith(settings.present_working_directory) and not file_path.startswith("/tmp/"):
            return EditFileResult(success=False, error="File is not allowed to be edited outside the present working directory")
        if not os.access(file_path, os.W_OK):
            return EditFileResult(success=False, error="File is not writable")
        
        # Validate old_content and new_content are different
        if old_content == new_content:
            return EditFileResult(success=False, error="Old content and new content are the same, no changes needed")
        
        stat_result = os.stat(file_path)
        if stat_result.st_size > settings.file_size_limit:
            return EditFileResult(success=False, error="File is too large to be edited")
        
        file_type = await get_file_type(file_path)
        if file_type != "text":
            return EditFileResult(success=False, error="File is not a text file")
        
        file_content = await read_file_content(file_path)
        
        # Normalize newlines BEFORE checking content to ensure consistent matching
        file_content = await normalize_newlines(file_content)
        old_content = await normalize_newlines(old_content)
        new_content = await normalize_newlines(new_content)

        if old_content not in file_content:
            return EditFileResult(success=False, error="Old content is not present in the file")

        file_content = await safe_replace(file_content, old_content, new_content, replace_all)

        await write_file_content(file_path, file_content)

        return EditFileResult(success=True, content=f"File {file_path} has been edited successfully")

    except Exception as e:
        return EditFileResult(success=False, error=f"Error editing file: {e}")