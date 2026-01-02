from base.settings import settings
from rich.table import Table
from rich.panel import Panel
from anyio import Path
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
    ) -> Panel:
    """Generates a human-readable summary of the list_todos action."""
    titles = [todo.title for todo in todo_store.get(task_group, {}).values()]
    table = Table(show_header=False, box=None, padding=(0, 1))  # Changed from (0, 0) to (0, 1)
    table.add_column("Status", justify="left", width=2)  # Changed from width=0 to width=2
    table.add_column("Task")

    for i, todo in enumerate(titles, 1):
        table.add_row("☐", todo)

    return Panel(
        table,
        title=f"[bold {settings.ai_color}]✓ Created {len(titles)} todos in '{task_group}'[/bold {settings.ai_color}]",
        border_style=settings.theme_color,
        padding=(1, 2)  # Changed from (0, 1) to (1, 2) for better spacing
    )