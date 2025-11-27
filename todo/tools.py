from typing import Annotated, Literal
from pydantic import BaseModel
from langchain_core.tools import tool


class TodoItem(BaseModel):
    id: int
    task_group: str
    title: str
    status: Literal["pending", "completed", "cancelled"] = "pending"

todo_store: dict[str, dict[int, TodoItem]] = {}

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
        Confirmation message that the todo was created successfully
    
    Example usage:
        When starting a data analysis task, first create todos for:
        1. Load and validate input data
        2. Perform statistical analysis
        3. Generate visualizations
        4. Compile final report
    """
    if task_group not in todo_store:
        todo_store[task_group] = {}

    todo_store[task_group][title] = TodoItem(
        id=len(todo_store[task_group]) + 1,
        title=title,
        task_group=task_group,
        status="pending"
    )
    return f'Todo created successfully'

@tool
def list_todos(task_group: Annotated[str, "The task_group of the todo item"]) -> str:
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

@tool
def delete_todo(
    task_group: Annotated[str, "The task_group of the todo item"],
    todo_id: Annotated[int, "The ID of the todo item to delete"]
) -> str:
    """Delete a todo item by its title from a specific task_group.
    
    This tool removes a todo permanently from the tracking system.
    Use this tool to:
    - Remove duplicate todos that were created by mistake
    - Clean up incorrectly created todos before starting work
    - Remove todos that were created with wrong information (task_group, title, etc.)
    
    Best practices:
    - AVOID using this during active work - prefer update_todo with 'cancelled' status instead to maintain history
    - Only delete todos for corrections, not for marking work as complete
    - Use update_todo to mark tasks as 'completed' or 'cancelled' rather than deleting them
    - Keep a record of what was planned, even if cancelled, for audit purposes
    
    NOTE: Deleting removes all record of the todo. For completed work, use update_todo with status='completed' instead.
    
    Args:
        task_group: The task_group name the todo belongs to
        todo_id: The ID of the todo item to delete
    
    Returns:
        Confirmation message that the todo was deleted successfully
    
    Example usage:
        If you accidentally created a duplicate todo 'Load data' twice, delete one:
        delete_todo(task_group='analysis-pipeline', todo_id=1)
    """
    task_group_todos = todo_store.get(task_group, {})
    todo = task_group_todos.get(todo_id)
    if not todo:
        return f"Todo with ID {todo_id} not found."
    task_group_todos.pop(todo_id)
    return f"Todo with ID {todo_id} deleted successfully."

TODO_TOOLS = [
    create_todo,
    list_todos,
    update_todo,
    delete_todo,
]