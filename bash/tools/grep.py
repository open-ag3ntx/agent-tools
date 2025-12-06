

import asyncio
import os
from typing import Annotated, Literal, Optional

from base.models import GrepToolResult
from base.settings import settings


async def grep(
    pattern: Annotated[str, "The regular expression pattern to search for in file contents"],
    path: Annotated[Optional[str], "File or directory to search in (rg PATH). Defaults to current working directory."],
    A: Annotated[Optional[int], "Number of lines to show before each match (rg -B). Requires output_mode: \"content\", ignored otherwise."],
    B: Annotated[Optional[int], "Number of lines to show after each match (rg -A). Requires output_mode: \"content\", ignored otherwise."],
    C: Annotated[Optional[int], "Number of lines to show before and after each match (rg -C). Requires output_mode: \"content\", ignored otherwise."],
    type: Annotated[Optional[str], "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."],
    glob: Annotated[Optional[str], "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"],
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
    
    if output_mode is None:
        output_mode = "files_with_matches"
    
    command_with_args = ['grep', pattern]

    if i:
        command_with_args.append('-i')
    if multiline:
        command_with_args.append('-U')
        command_with_args.append('--multiline-dotall')
    if n:
        command_with_args.append('-n')
    if offset:
        command_with_args.append(f'-offset {offset}')
    if head_limit:
        command_with_args.append(f'-head_limit {head_limit}')
    if A:
        command_with_args.append(f'-A {A}')
    if B:
        command_with_args.append(f'-B {B}')
    if C:
        command_with_args.append(f'-C {C}')
    if type:
        command_with_args.append(f'--type {type}')
    if glob:
        command_with_args.append(f'--glob {glob}')
    if output_mode:
        command_with_args.append(f'--output_mode {output_mode}')
    if path:
        command_with_args.append(path)
    if pattern:
        command_with_args.append(pattern)

    process = await asyncio.create_subprocess_exec(
        *command_with_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=path,
        env={'PATH': '/usr/bin:/bin'}
    )
    stdout, stderr = await process.communicate()
    stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
    stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
    return GrepToolResult(
        success=process.returncode == 0,
        stdout=stdout_str,
        stderr=stderr_str[:30000], # return only first 30000 characters of stderr
        return_code=process.returncode,
        command=command_with_args,
    )