import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Default timeout for commands (in seconds)
    default_timeout: int = 120
    
    # Maximum timeout allowed
    max_timeout: int = 300
    
    
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

    file_size_limit: int = 10 * 1024 * 1024 # 10MB
    max_lines_to_read: int = 2000
    max_length_of_line: int = 2000

    # present working directory of the user
    present_working_directory: str = os.getcwd()

    # present test directory
    os.makedirs(f"{present_working_directory}/test", exist_ok=True)
    present_test_directory: str = f"{present_working_directory}/test"

    # platform
    platform: str = os.uname().sysname
    # os version
    os_version: str = os.uname().release
    # is git repo    
    is_git_repo: bool = os.path.exists(f"{present_working_directory}/.git")


settings = Settings()

