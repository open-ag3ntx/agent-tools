import pytest

from todo.tools import create_todo, list_todos
from base.store import todo_store, _id_counter


@pytest.fixture(autouse=True)
def clear_todo_store():
    """Clear the todo store and ID counter before and after each test."""
    todo_store.clear()
    _id_counter.clear()
    yield
    todo_store.clear()
    _id_counter.clear()


class TestListTodos:
    """Tests for list_todos function."""

    def test_list_todos_empty_group(self):
        """Should return message when no todos exist."""
        result = list_todos.invoke({"task_group": "empty-group"})
        
        assert "No todos found" in result

    def test_list_todos_returns_all_todos(self):
        """Should return all todos for a task group."""
        create_todo.invoke({"titles": ["Task 1", "Task 2"], "task_group": "project"})
        
        result = list_todos.invoke({"task_group": "project"})
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        assert result[1].title == "Task 1"
        assert result[2].title == "Task 2"

    def test_list_todos_only_returns_specified_group(self):
        """Should only return todos from the specified group."""
        create_todo.invoke({"titles": ["Frontend task", "Backend task"], "task_group": "frontend"})
        
        frontend_todos = list_todos.invoke({"task_group": "frontend"})
        
        assert frontend_todos[1].title == "Frontend task"
        assert frontend_todos[2].title == "Backend task"
        assert len(frontend_todos) == 2

    def test_list_todos_shows_status(self):
        """Should show the status of each todo."""
        create_todo.invoke({"titles": ["Task 1"], "task_group": "project"})
        
        result = list_todos.invoke({"task_group": "project"})
        
        assert result[1].status == "pending"

    def test_list_todos_nonexistent_group(self):
        """Should handle nonexistent task group gracefully."""
        result = list_todos.invoke({"task_group": "nonexistent"})
        
        assert "No todos found" in result

