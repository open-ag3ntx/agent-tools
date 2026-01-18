import pytest

from todo.tools import create_todo, update_todo
from base.store import todo_store, _id_counter


@pytest.fixture(autouse=True)
def clear_todo_store():
    """Clear the todo store and ID counter before and after each test."""
    todo_store.clear()
    _id_counter.clear()
    yield
    todo_store.clear()
    _id_counter.clear()


class TestUpdateTodo:
    """Tests for update_todo function."""

    def test_update_todo_to_completed(self):
        """Should update todo status to completed."""
        create_todo.invoke({"titles": ["Task"], "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        
        assert "successfully" in result.lower()
        assert todo_store["project"][1].status == "completed"




    def test_update_todo_to_cancelled(self):
        """Should update todo status to cancelled."""
        create_todo.invoke({"titles": ["Task"], "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "cancelled"})
        
        assert "successfully" in result.lower()
        assert todo_store["project"][1].status == "cancelled"

    def test_update_todo_back_to_pending(self):
        """Should allow resetting status to pending."""
        create_todo.invoke({"titles": ["Task"], "task_group": "project"})
        
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "pending"})
        
        assert todo_store["project"][1].status == "pending"

    def test_update_nonexistent_todo(self):
        """Should return error for nonexistent todo."""
        create_todo.invoke({"titles": ["Task"], "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 999, "status": "completed"})
        
        assert "not found" in result.lower()

    def test_update_todo_wrong_group(self):
        """Should return error when task group is wrong."""
        create_todo.invoke({"titles": ["Task"], "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "wrong-group", "todo_id": 1, "status": "completed"})
        
        assert "not found" in result.lower()

    def test_update_multiple_todos(self):
        """Should update multiple todos independently."""
        create_todo.invoke({"titles": ["Task 1", "Task 2"], "task_group": "project"})
        
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        
        assert todo_store["project"][1].status == "completed"
        assert todo_store["project"][2].status == "pending"

