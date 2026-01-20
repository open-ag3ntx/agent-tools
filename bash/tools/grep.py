import asyncio
import os
from typing import Annotated, Literal, Optional

from base.models import GrepToolResult
from base.settings import settings

# check how many times grep is called
async def grep(
    pattern: Annotated[str, "The regular expression pattern to search for in file contents"],
    path: Annotated[Optional[str], "File or directory to search in (rg PATH). Defaults to current working directory."] = None,
    A: Annotated[Optional[int], "Number of lines to show after each match (rg -A). Requires output_mode: \"content\", ignored otherwise."] = None,
    B: Annotated[Optional[int], "Number of lines to show before each match (rg -B). Requires output_mode: \"content\", ignored otherwise."] = None,
    C: Annotated[Optional[int], "Number of lines to show before and after each match (rg -C). Requires output_mode: \"content\", ignored otherwise."] = None,
    type: Annotated[Optional[str], "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."] = None,
    glob: Annotated[Optional[str], "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"] = None,
    output_mode: Annotated[Literal["content", "files_with_matches", "count"], "Output mode: \"content\" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), \"files_with_matches\" shows file paths (supports head_limit), \"count\" shows match counts (supports head_limit). Defaults to \"files_with_matches\"."] = "files_with_matches",
    i: Annotated[Optional[bool], "Case insensitive search (rg -i)"] = True,
    multiline: Annotated[Optional[bool], "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false."] = False,
    n: Annotated[Optional[bool], "Show line numbers in output (rg -n). Requires output_mode: \"content\", ignored otherwise. Defaults to true."] = True,
    offset: Annotated[Optional[int], "Skip first N lines/entries before applying head_limit, equivalent to \"| tail -n +N | head -N\". Works across all output modes. Defaults to 0."] = 0,
    head_limit: Annotated[Optional[int], "Limit output to first N lines/entries, equivalent to \"| head -N\". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). Defaults based on \"cap\" experiment value: 1000"] = 1000,
) -> GrepToolResult:
    """
    A powerful search tool built on ripgrep
    Usage:
    - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.
    - Supports full regex syntax (e.g., \"log.*Error\", \"function\\s+\\w+\")
    - Filter files with glob parameter (e.g., \"*.js\", \"**/*.tsx\") or type parameter (e.g., \"js\", \"py\", \"rust\")
    - Output modes: \"content\" shows matching lines, \"files_with_matches\" shows only file paths (default), \"count\" shows match counts
    - Use Task tool for open-ended searches requiring multiple rounds
    - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)
    - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline: true`
    """

    # Validate and set default path
    if path is None:
        path = settings.present_test_directory
    
    if not os.path.exists(path):
        return GrepToolResult(
            success=False,
            error=f"Path does not exist: {path}",
        )
    
    if not path.startswith(settings.present_test_directory):
        return GrepToolResult(
            success=False,
            error=f"Path is not in the present working directory: {path}",
        )
    
    # Validate pattern
    if not pattern:
        return GrepToolResult(
            success=False,
            error="Pattern is required",
        )
    
    # Build ripgrep command
    command_with_args = ['rg']
    
    # Add output mode flags
    if output_mode == "files_with_matches":
        command_with_args.append('-l')
    elif output_mode == "count":
        command_with_args.append('-c')
    # For "content" mode, no special flag needed (default behavior)

    # Add case insensitivity flag
    if i:
        command_with_args.append('-i')
    
    # Add multiline flags
    if multiline:
        command_with_args.extend(['-U', '--multiline-dotall'])
    
    # Add line numbers for content mode
    if n and output_mode == "content":
        command_with_args.append('-n')
    
    # Add context flags (only for content mode)
    if output_mode == "content":
        if A is not None:
            command_with_args.extend(['-A', str(A)])
        if B is not None:
            command_with_args.extend(['-B', str(B)])
        if C is not None:
            command_with_args.extend(['-C', str(C)])
    
    # Add type filter
    if type:
        command_with_args.extend(['--type', type])
    
    # Add glob filter
    if glob:
        command_with_args.extend(['--glob', glob])
    
    # Add pattern and path
    command_with_args.append(pattern)
    command_with_args.append(path)

    # Determine working directory (use directory, not file)
    working_dir = path if os.path.isdir(path) else os.path.dirname(path)
    if not working_dir:
        working_dir = settings.present_test_directory

    try:
        process = await asyncio.create_subprocess_exec(
            *command_with_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )
        stdout, stderr = await process.communicate()
    except FileNotFoundError:
        return GrepToolResult(
            success=False,
            error="ripgrep (rg) is not installed or not in PATH",
        )
    except Exception as e:
        return GrepToolResult(
            success=False,
            error=f"Failed to execute ripgrep: {str(e)}",
        )
    
    stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
    stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
    
    lines = stdout_str.strip().split('\n') if stdout_str.strip() else []
    
    if offset and offset > 0:
        lines = lines[offset:]
    
    if head_limit and head_limit > 0:
        lines = lines[:head_limit]
    
    result_files = []
    result_lines = []
    result_counts = 0
    
    if output_mode == "files_with_matches":
        result_files = [line.strip() for line in lines if line.strip()]
    elif output_mode == "count":
        for line in lines:
            if line.strip():
                if ':' in line:
                    try:
                        count = int(line.split(':')[-1])
                        result_counts += count
                    except ValueError:
                        pass
                else:
                    try:
                        result_counts += int(line.strip())
                    except ValueError:
                        pass
    else:  # content mode
        result_lines = lines
    
    success = process.returncode in (0, 1)
    
    if process.returncode >= 2:
        return GrepToolResult(
            success=False,
            error=stderr_str[:30000] if stderr_str else "ripgrep command failed",
        )
    
    return GrepToolResult(
        success=success,
        lines=result_lines,
        files=result_files,
        counts=result_counts,
    )

def display_grep(
    pattern: Annotated[str, "The regular expression pattern to search for in file contents"],
    path: Annotated[Optional[str], "File or directory to search in (rg PATH). Defaults to current working directory."] = None,
    A: Annotated[Optional[int], "Number of lines to show after each match (rg -A). Requires output_mode: \"content\", ignored otherwise."] = None,
    B: Annotated[Optional[int], "Number of lines to show before each match (rg -B). Requires output_mode: \"content\", ignored otherwise."] = None,
    C: Annotated[Optional[int], "Number of lines to show before and after each match (rg -C). Requires output_mode: \"content\", ignored otherwise."] = None,
    type: Annotated[Optional[str], "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."] = None,
    glob: Annotated[Optional[str], "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"] = None,
    output_mode: Annotated[Literal["content", "files_with_matches", "count"], "Output mode: \"content\" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), \"files_with_matches\" shows file paths (supports head_limit), \"count\" shows match counts (supports head_limit). Defaults to \"files_with_matches\"."] = "files_with_matches",
    i: Annotated[Optional[bool], "Case insensitive search (rg -i)"] = True,
    multiline: Annotated[Optional[bool], "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false."] = False,
    n: Annotated[Optional[bool], "Show line numbers in output (rg -n). Requires output_mode: \"content\", ignored otherwise. Defaults to true."] = True,
    offset: Annotated[Optional[int], "Skip first N lines/entries before applying head_limit, equivalent to \"| tail -n +N | head -N\". Works across all output modes. Defaults to 0."] = 0,
    head_limit: Annotated[Optional[int], "Limit output to first N lines/entries, equivalent to \"| head -N\". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). Defaults based on \"cap\" experiment value: 1000"] = 1000,
) -> str:
    """Generates a human-readable summary of the grep action."""
    return f'Grep Pattern: {pattern} in Path: {path or settings.present_test_directory} (Output Mode: {output_mode})'