from typing import Annotated
from langchain_core.tools import tool
from base.store import _get_next_id, todo_store
from base.models import TodoItem


@tool
def create_todo(
    title: Annotated[str, "The title of the todo item"],
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
    - Create a todo for the overall task completion as a final checkpoint
    
    Args:
        title: A clear, descriptive title for the todo item (e.g., 'Step 1: Initialize database connection')
        task_group: The task_group or workflow name this todo belongs to (e.g., 'data-pipeline-2024')
    
    Returns:
        Confirmation message with the todo ID
    
    Example usage:
        When starting a data analysis task, first create todos for:
        1. Load and validate input data
        2. Perform statistical analysis
        3. Generate visualizations
        4. Compile final report
    """
    if task_group not in todo_store:
        todo_store[task_group] = {}

    todo_id = _get_next_id(task_group)
    todo_store[task_group][todo_id] = TodoItem(
        id=todo_id,
        title=title,
        task_group=task_group,
        status="pending"
    )
    return f'Todo created successfully with ID {todo_id}'
