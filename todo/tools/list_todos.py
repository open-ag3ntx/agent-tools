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
    ) -> str:
    """Generates a human-readable summary of the list_todos action."""
    todo_str = ''
    todos = todo_store.get(task_group, {})
    if not todos:
        return f'No todos found for task group: {task_group}'
    todo_items = []
    for todo in todos.values():
        # Markdown task list requires: - [ ] or - [x]
        if todo.status == 'completed':
            status_icon = '-[x]'
        else:
            status_icon = '-[ ]'
        
        todo_items.append(f'{status_icon} {todo.title}')
    todo_str = "\n".join(todo_items)
    result = f'Todo Items for Task Group: {task_group}\n{todo_str}'
    print('=================DEBUG LIST TODOS SUMMARY=================')
    print(result)
    print('==========================================================')
    return result

def test_display_list_todos():
    # Setup test data
    task_group = "test_group"
    todo_store[task_group] = {
        1: TodoItem(id=1, task_group=task_group, title="First Task", status="pending"),
        2: TodoItem(id=2, task_group=task_group, title="Second Task", status="completed"),
        3: TodoItem(id=3, task_group=task_group, title="Third Task", status="cancelled"),
    }
    
    # Call the display function
    summary = display_list_todos(task_group)
    
    # Print the summary for visual inspection
    print(summary)

if __name__ == "__main__":
    test_display_list_todos()