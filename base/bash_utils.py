from base.settings import settings
from typing import Optional


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

