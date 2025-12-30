
from typing import Annotated
from langchain_core.tools import tool
from base.store import _get_next_id, todo_store
from base.models import TodoItem


@tool
def create_todo(
    titles: Annotated[list[str], "The titles of the todo items to create"],
    task_group: Annotated[str, "The task_group of the todo item"]
) -> str:
    """Create a new todo item and add it to the todo list for tracking long-running tasks.
    
    This tool is essential for managing multi-step processes and ensuring no steps are missed.
    Use this tool to:
    - Break down complex tasks into trackable subtasks at the start of any long-running operation
    - Create checkpoints for each major step in a workflow (e.g., 'Analyze data', 'Generate report', 'Send notification')
    - Document action items that need to be completed sequentially or in parallel
    - Keep track of what has been done and what remains to be done in extended operations
    
    Best practices:
    - Create todos BEFORE starting work on each step, not after
    - Use clear, action-oriented titles (e.g., 'Fetch user data from API' rather than 'User data')
    - Group related todos under the same task_group name for organization
    - Create todos for the overall task completion as a final checkpoint
    
    Args:
        titles: A list of clear, descriptive titles for the todo items (e.g., ['Step 1: Initialize database connection', 'Step 2: Fetch user data from API'])
        task_group: The task_group or workflow name this todo belongs to (e.g., 'data-pipeline-2024')
    
    Returns:
        Confirmation message with the todo IDs
    
    Example usage:
        When starting a data analysis task, first create todos for:
        1. Load and validate input data
        2. Perform statistical analysis
        3. Generate visualizations
        4. Compile final report
    """
    if task_group not in todo_store:
        todo_store[task_group] = {}
    todo_ids = []
    for title in titles:
        todo_id = _get_next_id(task_group)
        todo_store[task_group][todo_id] = TodoItem(
            id=todo_id,
            title=title,
            task_group=task_group,
            status="pending"
        )
        todo_ids.append(todo_id)
    return f'Todos created successfully with IDs {todo_ids}'


from rich.console import Console
from rich.table import Table

def display_create_todo(
    titles: list[str],
    task_group: str,
) -> str:
    """Displays todos in a table format with checkboxes."""
    
    console = Console()
    
    table = Table(title=f"Todo Items for Task Group: {task_group}", 
                  show_header=True, 
                  header_style="bold cyan")
    
    table.add_column("Status", style="dim", width=8)
    table.add_column("Task", style="white")
    
    for todo in titles:
        table.add_row("☐", todo)  # Use unicode checkbox
    
    # Return as string for markdown rendering
    result = f'**Todo Items for Task Group: {task_group}**\n\n'
    for todo in titles:
        result += f'☐ {todo}\n'
    
    return result