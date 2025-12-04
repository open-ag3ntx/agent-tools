import asyncio
import json
import os
from pathlib import Path
from typing import Annotated
from base.models import GlobToolResult
from base.settings import settings
import glob as glob_lib


async def glob(
    pattern: Annotated[str, "The glob pattern to match files against"],
    path: Annotated[str, "The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter \"undefined\" or \"null\" - simply omit it for the default behavior. Must be a valid directory path if provided."],
) -> GlobToolResult:
    """
    - Fast file pattern matching tool that works with any codebase size
    - Supports glob patterns like \"**/*.js\" or \"src/**/*.ts\"
    - Returns matching file paths sorted by modification time
    - Use this tool when you need to find files by name patterns
    - Always run glob with strict pattern matching first to get the top level files, then run glob with recursive pattern matching to get the subdirectories and files within them to avoid globbing the .git, venv, node_modules, etc directories.
    - When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
    - You can call multiple tools in a single response. It is always better to speculatively perform multiple searches in parallel if they are potentially useful.
    """
    try:
        # Determine the working directory
        cwd = path or settings.present_test_directory
        if not os.path.exists(cwd):
            return GlobToolResult(
                success=False,
                error=f"Working directory does not exist: {cwd}",
            )
        if not os.path.isdir(cwd):
            return GlobToolResult(
                success=False,
                error=f"Path is not a directory: {cwd}",
            )
        
        if not cwd.startswith(settings.present_test_directory):
            return GlobToolResult(
                success=False,
                error=f"Path is not in the present working directory: {cwd}",
            )
        
        files = Path(cwd).glob(pattern, recurse_symlinks=False, case_sensitive=False)
        files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        files = [str(file) for file in files]
        # TODO filter outl files based on gitignore
        return GlobToolResult(
            success=True,
            files=files
        )
    except Exception as e:
        return GlobToolResult(
            success=False,
            error=f"Error searching for files: {str(e)}"
        )
