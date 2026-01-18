from base.models import TodoItem
from typing import Dict, Any
# Store todos keyed by task_group -> id -> TodoItem
todo_store: Dict[str, Dict[int, TodoItem]] = {}
# Track next ID per task_group (persists across deletions)
_id_counter: Dict[str, int] = {}




def _get_next_id(task_group: str) -> int:
    """Get the next available ID for a task group."""
    if task_group not in _id_counter:
        _id_counter[task_group] = 0
    _id_counter[task_group] += 1
    return _id_counter[task_group]