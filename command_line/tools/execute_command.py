import asyncio
import os
import shlex
from typing import Annotated, Optional

from base.settings import settings
from base.models import CommandResult


def is_command_blocked(command: str) -> bool:
    """Check if a command is in the blocked list."""
    command_lower = command.lower().strip()
    for blocked in settings.blocked_commands:
        if blocked.lower() in command_lower:
            return True
    return False


def is_command_dangerous(command: str) -> Optional[str]:
    """Check if a command matches dangerous patterns. Returns the pattern if found."""
    command_lower = command.lower().strip()
    for pattern in settings.dangerous_patterns:
        if pattern.lower() in command_lower:
            return pattern
    return None


def is_directory_allowed(directory: str) -> bool:
    """Check if the directory is in the allowed list."""
    abs_directory = os.path.abspath(directory)
    for allowed in settings.allowed_directories:
        abs_allowed = os.path.abspath(allowed)
        if abs_directory.startswith(abs_allowed):
            return True
    if not abs_directory.startswith(settings.present_working_directory):
        return False
    return False


async def execute_command(
    command: Annotated[str, "The shell command to execute"],
    working_directory: Annotated[Optional[str], "The directory to run the command in (defaults to current working directory)"] = None,
    timeout: Annotated[Optional[int], "Timeout in seconds (default: 60, max: 300)"] = None,
) -> CommandResult:
    """
    Execute a shell command and return the result.
    
    This tool runs shell commands in a subprocess and captures stdout, stderr, and return code.
    
    Security features:
    - Commands are executed in a controlled working directory
    - Dangerous commands are blocked or flagged
    - Timeout prevents runaway processes
    
    Use this for:
    - Running build commands (npm install, pip install, etc.)
    - Git operations
    - File system operations that require shell
    - Running scripts and programs
    """
    try:
        # Validate and set working directory
        if working_directory is None:
            working_directory = settings.working_directory
        
        # Ensure working directory exists
        if not os.path.exists(working_directory):
            return CommandResult(
                success=False,
                error=f"Working directory does not exist: {working_directory}",
                command=command
            )
        
        if not os.path.isdir(working_directory):
            return CommandResult(
                success=False,
                error=f"Path is not a directory: {working_directory}",
                command=command
            )
        
        # Check if directory is allowed
        if not is_directory_allowed(working_directory):
            return CommandResult(
                success=False,
                error=f"Command execution not allowed in directory: {working_directory}",
                command=command,
                working_directory=working_directory
            )
        
        # Check if command is blocked
        if is_command_blocked(command):
            return CommandResult(
                success=False,
                error=f"Command is blocked for security reasons: {command}",
                command=command,
                working_directory=working_directory
            )
        
        # Check for dangerous patterns (warn but allow)
        dangerous_pattern = is_command_dangerous(command)
        warning = None
        if dangerous_pattern:
            warning = f"Warning: Command contains potentially dangerous pattern '{dangerous_pattern}'"
        
        # Set timeout
        if timeout is None:
            timeout = settings.default_timeout
        timeout = min(timeout, settings.max_timeout)
        
        # Execute the command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_directory
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Add warning to stderr if dangerous pattern detected
            if warning:
                stderr_str = f"{warning}\n{stderr_str}" if stderr_str else warning
            
            return CommandResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode,
                command=command,
                working_directory=working_directory,
                error=stderr_str if process.returncode != 0 else None
            )
            
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            await process.wait()
            
            return CommandResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                command=command,
                working_directory=working_directory,
                timed_out=True
            )
    
    except Exception as e:
        return CommandResult(
            success=False,
            error=f"Error executing command: {str(e)}",
            command=command,
            working_directory=working_directory if working_directory else settings.working_directory
        )

