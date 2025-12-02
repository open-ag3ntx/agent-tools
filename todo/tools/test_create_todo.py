import pytest

from todo.tools import create_todo
from base.store import todo_store, _id_counter


@pytest.fixture(autouse=True)
def clear_todo_store():
    """Clear the todo store and ID counter before and after each test."""
    todo_store.clear()
    _id_counter.clear()
    yield
    todo_store.clear()
    _id_counter.clear()


class TestCreateTodo:
    """Tests for create_todo function."""

    def test_create_single_todo(self):
        """Should create a single todo item."""
        result = create_todo.invoke({"title": "Test task", "task_group": "test-group"})
        
        assert "successfully" in result.lower()
        assert "test-group" in todo_store
        assert 1 in todo_store["test-group"]
        assert todo_store["test-group"][1].title == "Test task"

    def test_create_todo_has_correct_properties(self):
        """Should create todo with correct properties."""
        create_todo.invoke({"title": "My task", "task_group": "my-group"})
        
        todo = todo_store["my-group"][1]
        assert todo.title == "My task"
        assert todo.task_group == "my-group"
        assert todo.status == "pending"
        assert todo.id == 1

    def test_create_multiple_todos_in_same_group(self):
        """Should create multiple todos in the same task group."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        create_todo.invoke({"title": "Task 2", "task_group": "project"})
        create_todo.invoke({"title": "Task 3", "task_group": "project"})
        
        assert len(todo_store["project"]) == 3
        assert todo_store["project"][1].title == "Task 1"
        assert todo_store["project"][2].title == "Task 2"
        assert todo_store["project"][3].title == "Task 3"

    def test_create_todos_in_different_groups(self):
        """Should create todos in different task groups."""
        create_todo.invoke({"title": "Frontend task", "task_group": "frontend"})
        create_todo.invoke({"title": "Backend task", "task_group": "backend"})
        
        assert "frontend" in todo_store
        assert "backend" in todo_store
        assert todo_store["frontend"][1].title == "Frontend task"
        assert todo_store["backend"][1].title == "Backend task"

    def test_create_todo_increments_id(self):
        """Should increment ID for each new todo in a group."""
        create_todo.invoke({"title": "Task 1", "task_group": "group"})
        create_todo.invoke({"title": "Task 2", "task_group": "group"})
        
        assert todo_store["group"][1].id == 1
        assert todo_store["group"][2].id == 2

    def test_create_todo_with_special_characters_in_title(self):
        """Should handle special characters in title."""
        create_todo.invoke({"title": "Task: with 'special' chars & symbols!", "task_group": "group"})
        
        assert todo_store["group"][1].title == "Task: with 'special' chars & symbols!"

    def test_create_todo_with_unicode_title(self):
        """Should handle unicode in title."""
        create_todo.invoke({"title": "任务 📝", "task_group": "unicode-group"})
        
        assert todo_store["unicode-group"][1].title == "任务 📝"

    def test_create_duplicate_title_creates_separate_todos(self):
        """Should create separate todos even with same title."""
        create_todo.invoke({"title": "Duplicate", "task_group": "group"})
        create_todo.invoke({"title": "Duplicate", "task_group": "group"})
        
        # Each creation gets a unique ID
        assert len(todo_store["group"]) == 2
        assert todo_store["group"][1].title == "Duplicate"
        assert todo_store["group"][2].title == "Duplicate"

    def test_create_returns_id_in_message(self):
        """Should return the todo ID in the success message."""
        result = create_todo.invoke({"title": "Task", "task_group": "group"})
        
        assert "ID 1" in result or "id 1" in result.lower()

    def test_empty_title(self):
        """Should handle empty title."""
        create_todo.invoke({"title": "", "task_group": "group"})
        
        assert 1 in todo_store["group"]
        assert todo_store["group"][1].title == ""

    def test_empty_task_group(self):
        """Should handle empty task group."""
        create_todo.invoke({"title": "Task", "task_group": ""})
        
        assert "" in todo_store
        assert todo_store[""][1].title == "Task"

    def test_whitespace_in_title(self):
        """Should preserve whitespace in title."""
        create_todo.invoke({"title": "  Spaced Task  ", "task_group": "group"})
        
        assert todo_store["group"][1].title == "  Spaced Task  "

    def test_long_title(self):
        """Should handle long titles."""
        long_title = "A" * 1000
        create_todo.invoke({"title": long_title, "task_group": "group"})
        
        assert todo_store["group"][1].title == long_title

    def test_special_characters_in_group(self):
        """Should handle special characters in task group."""
        create_todo.invoke({"title": "Task", "task_group": "group-with_special.chars!"})
        
        assert "group-with_special.chars!" in todo_store
        assert todo_store["group-with_special.chars!"][1].title == "Task"

