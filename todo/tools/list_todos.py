from base.models import TodoItem
from typing import Annotated
from langchain_core.tools import tool
from base.store import todo_store


@tool
def list_todos(task_group: Annotated[str, "The task_group of the todo item"]) -> dict[int, TodoItem] | str:
    """List all todos for a specific task_group to review progress and identify remaining work.
    
    This tool is critical for maintaining awareness of task status during long-running operations.
    Use this tool to:
    - Check which tasks have been completed and which are still pending before proceeding
    - Verify that all planned steps have been created and tracked
    - Review the current state of a multi-step process at any point
    - Identify the next pending task that needs to be worked on
    - Ensure no steps are skipped or forgotten in complex workflows
    
    Best practices:
    - Check todos at the START of resuming work to see what's been done
    - Review todos DURING long operations to stay on track
    - List todos BEFORE marking a task_group complete to ensure nothing is missed
    - Use this frequently to prevent deviation from the planned workflow
    
    Args:
        task_group: The task_group name to list todos for (must match the task_group name used when creating todos)
    
    Returns:
        Dictionary of all todos for the task_group with their IDs, titles, and statuses, or a message if no todos exist
    
    Example usage:
        Before continuing a data pipeline task, list todos to see:
        - Which data sources have been processed
        - Which validation steps remain
        - What the next pending action is
    """
    todos = todo_store.get(task_group, {})
    if not todos:
        return "No todos found for this task_group. Create a todo first."
    return todos

def display_list_todos(
    task_group: str,
    ) -> str:
    """Generates a human-readable summary of the list_todos action."""
    todo_str = ''
    todos = todo_store.get(task_group, {})
    if not todos:
        return f'No todos found for task group: {task_group}'
    for todo in todos.values():
        status_icon = '- [x]' if todo.status == 'completed' else '- [ ]' if todo.status == 'cancelled' else '- [ ]'
        todo_str += f'- {status_icon} [{todo.id}] {todo.title} ({todo.status})\n'
    return f'Todo Items for Task Group: {task_group}\n{todo_str}'