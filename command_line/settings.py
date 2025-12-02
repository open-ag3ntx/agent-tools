import os
from pydantic_settings import BaseSettings
from typing import List


class CommandLineSettings(BaseSettings):
    # Default timeout for commands (in seconds)
    default_timeout: int = 60
    
    # Maximum timeout allowed
    max_timeout: int = 300
    
    # Present working directory (project root)
    present_working_directory: str = os.getcwd()
    
    # Working directory for command execution
    working_directory: str = f"{os.getcwd()}/test"
    
    # Allowed directories for command execution
    allowed_directories: List[str] = [f"{os.getcwd()}/test", "/tmp"]
    
    # Dangerous commands that are blocked by default
    blocked_commands: List[str] = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",
        "mv /* /dev/null",
        "wget -O- | sh",
        "curl | sh",
    ]
    
    # Commands that require confirmation (not blocked, but flagged)
    dangerous_patterns: List[str] = [
        "rm -rf",
        "sudo",
        "chmod 777",
        "chown",
        "> /dev/",
        "dd ",
        "mkfs",
        "fdisk",
        "shutdown",
        "reboot",
        "init ",
    ]


settings = CommandLineSettings()

