import asyncio
import json
import os
from pathlib import Path
from typing import Annotated, Optional
from base.models import GlobToolResult
from base.settings import settings
import glob as glob_lib


async def glob(
    pattern: Annotated[str, "The glob pattern to match files against"],
    path: Annotated[str, "The absolute directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter \"undefined\" or \"null\" - simply omit it for the default behavior. Must be a valid directory path if provided."],
    exclude_dirs: Annotated[list[str], "List of directory names to exclude from the search (e.g., ['__pycache__', 'node_modules', 'venv'])"] = [],
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
                error=f"Absolute working directory does not exist: {cwd}",
            )
        if not os.path.isdir(cwd):
            return GlobToolResult(
                success=False,
                error=f"Path is not a directory: {cwd}",
            )
        
        if not cwd.startswith(settings.present_test_directory):
            print(f"Denied globbing outside present working directory: {cwd} vs {settings.present_test_directory}")
            return GlobToolResult(
                success=False,
                error=f"Path is not in the present working directory: {cwd}",
            )
        
        files = Path(cwd).glob(pattern, recurse_symlinks=False, case_sensitive=False)
        files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        files = [str(file) for file in files if all(excl not in file.parts for excl in exclude_dirs)]
        # TODO filter outl files based on gitignore
        
        total = len(files)
        skipped = 0  # Placeholder for future skipped files count based on gitignore

        files = files[:100]  # Limit to first 500 files to avoid massive outputs

        return GlobToolResult(
            success=True,
            files=files,
            total_files=total,
            skipped_files=total - len(files),
        )
    except Exception as e:
        return GlobToolResult(
            success=False,
            error=f"Error searching for files: {str(e)}"
        )
 
def display_glob(
    pattern: str,
    path: str | None = None,
    exclude_dirs: Optional[list[str]] = None,
) -> str:
    """Generates a human-readable summary of the glob action."""
    cwd = path or settings.present_test_directory
    return f'Globbing {pattern} in directory: {cwd} excluding directories: {exclude_dirs or []}'