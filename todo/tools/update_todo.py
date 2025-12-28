from typing import Annotated, Literal
from langchain_core.tools import tool
from base.store import todo_store


@tool
def update_todo(
    task_group: Annotated[str, "The task_group of the todo item"],
    todo_id: Annotated[int, "The ID of the todo item to update"],
    status: Annotated[Literal["pending", "completed", "cancelled"], "The status of the todo item"]
) -> str:
    """Update the status of a todo item to track progress through long-running tasks.
    
    This tool is vital for maintaining accurate progress tracking and preventing work duplication.
    Use this tool to:
    - Mark tasks as 'completed' immediately after finishing each step to track progress
    - Mark tasks as 'cancelled' if a step becomes unnecessary or is skipped due to changed requirements
    - Prevent re-doing work by clearly marking what's already been accomplished
    - Create a clear audit trail of what has been done in a multi-step process
    
    Best practices:
    - Update todo status IMMEDIATELY after completing each step, not at the end of all work
    - Always mark a todo as completed before moving to the next task in sequence
    - Use 'cancelled' status when skipping a step (don't delete - keep the record)
    - List todos after updating to confirm the change was applied correctly
    
    CRITICAL: Always update the todo for a step RIGHT AFTER completing it to maintain sync between actual work and tracked work.
    
    Args:
        task_group: The task_group name the todo belongs to
        todo_id: The numeric ID of the todo to update (obtained from list_todos)
        status: The new status - use 'completed' when done, 'cancelled' when skipping, 'pending' to reset
    
    Returns:
        Confirmation message that the todo was updated successfully
    
    Example usage:
        After successfully fetching data from an API:
        1. Complete the work
        2. Immediately call update_todo to mark 'Fetch API data' as completed
        3. List todos to confirm and see the next pending task
    """
    task_group_todos = todo_store.get(task_group, {})
    todo = task_group_todos.get(todo_id)
    if not todo:
        return f"Todo with ID {todo_id} not found."
    todo.status = status
    return f"Todo {todo_id} updated to status '{status}' successfully."

def display_update_todo(
    task_group: str,
    todo_id: int,
    status: Literal["pending", "completed", "cancelled"],
    ) -> str:
    """Generates a human-readable summary of the update_todo action."""
    return f'Updating Todo Item ID: {todo_id} in Task Group: {task_group} to Status: {status}'