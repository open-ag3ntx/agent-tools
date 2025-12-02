import os
from file_system.settings import settings
from file_system.models import BaseToolResult
from file_system.utils import get_file_type, normalize_newlines, read_file_content, safe_replace, write_file_content
from typing import Annotated, Optional

class EditFileResult(BaseToolResult):
    new_file_created: bool = False


async def edit_file(
    file_path: Annotated[str, "The absolute path to the file to edit"],
    old_string: Annotated[str, "The content to replace in the file must be different from the new content"],
    new_string: Annotated[str, "The content to replace the old content with"],
    replace_all: Annotated[Optional[bool], "Replace all occurrences of the old content, if False, only the first occurrence will be replaced"] = False,
    ) -> EditFileResult:
    """
    Performs exact string replacements in files. 
    Usage:
    - You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
    - When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. 
    - Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.
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
        
        # Validate old_string and new_string are different
        if old_string == new_string:
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
        old_string = await normalize_newlines(old_string)
        new_string = await normalize_newlines(new_string)

        if old_string not in file_content:
            return EditFileResult(success=False, error="Old content is not present in the file")

        file_content = await safe_replace(file_content, old_string, new_string, replace_all)

        await write_file_content(file_path, file_content)

        return EditFileResult(success=True, content=f"File {file_path} has been edited successfully")

    except Exception as e:
        return EditFileResult(success=False, error=f"Error editing file: {e}")