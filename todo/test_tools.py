import pytest
from unittest.mock import patch

from todo.tools import (
    create_todo,
    list_todos,
    update_todo,
    delete_todo,
    todo_store,
    _id_counter,
    TodoItem,
)


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


class TestListTodos:
    """Tests for list_todos function."""

    def test_list_todos_empty_group(self):
        """Should return message when no todos exist."""
        result = list_todos.invoke({"task_group": "empty-group"})
        
        assert "No todos found" in result

    def test_list_todos_returns_all_todos(self):
        """Should return all todos for a task group."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        create_todo.invoke({"title": "Task 2", "task_group": "project"})
        
        result = list_todos.invoke({"task_group": "project"})
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        assert result[1].title == "Task 1"
        assert result[2].title == "Task 2"

    def test_list_todos_only_returns_specified_group(self):
        """Should only return todos from the specified group."""
        create_todo.invoke({"title": "Frontend task", "task_group": "frontend"})
        create_todo.invoke({"title": "Backend task", "task_group": "backend"})
        
        frontend_todos = list_todos.invoke({"task_group": "frontend"})
        
        assert frontend_todos[1].title == "Frontend task"
        assert len(frontend_todos) == 1

    def test_list_todos_shows_status(self):
        """Should show the status of each todo."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        
        result = list_todos.invoke({"task_group": "project"})
        
        assert result[1].status == "pending"

    def test_list_todos_nonexistent_group(self):
        """Should handle nonexistent task group gracefully."""
        result = list_todos.invoke({"task_group": "nonexistent"})
        
        assert "No todos found" in result


class TestUpdateTodo:
    """Tests for update_todo function."""

    def test_update_todo_to_completed(self):
        """Should update todo status to completed."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        
        assert "successfully" in result.lower()
        assert todo_store["project"][1].status == "completed"

    def test_update_todo_to_cancelled(self):
        """Should update todo status to cancelled."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "cancelled"})
        
        assert "successfully" in result.lower()
        assert todo_store["project"][1].status == "cancelled"

    def test_update_todo_back_to_pending(self):
        """Should allow resetting status to pending."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "pending"})
        
        assert todo_store["project"][1].status == "pending"

    def test_update_nonexistent_todo(self):
        """Should return error for nonexistent todo."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "project", "todo_id": 999, "status": "completed"})
        
        assert "not found" in result.lower()

    def test_update_todo_wrong_group(self):
        """Should return error when task group is wrong."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = update_todo.invoke({"task_group": "wrong-group", "todo_id": 1, "status": "completed"})
        
        assert "not found" in result.lower()

    def test_update_multiple_todos(self):
        """Should update multiple todos independently."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        create_todo.invoke({"title": "Task 2", "task_group": "project"})
        
        update_todo.invoke({"task_group": "project", "todo_id": 1, "status": "completed"})
        
        assert todo_store["project"][1].status == "completed"
        assert todo_store["project"][2].status == "pending"


class TestDeleteTodo:
    """Tests for delete_todo function."""

    def test_delete_todo(self):
        """Should delete a todo item."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = delete_todo.invoke({"task_group": "project", "todo_id": 1})
        
        assert "successfully" in result.lower()
        assert 1 not in todo_store["project"]

    def test_delete_nonexistent_todo(self):
        """Should return error for nonexistent todo."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = delete_todo.invoke({"task_group": "project", "todo_id": 999})
        
        assert "not found" in result.lower()

    def test_delete_todo_wrong_group(self):
        """Should return error when task group is wrong."""
        create_todo.invoke({"title": "Task", "task_group": "project"})
        
        result = delete_todo.invoke({"task_group": "wrong-group", "todo_id": 1})
        
        assert "not found" in result.lower()

    def test_delete_one_of_multiple_todos(self):
        """Should only delete the specified todo."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        create_todo.invoke({"title": "Task 2", "task_group": "project"})
        
        delete_todo.invoke({"task_group": "project", "todo_id": 1})
        
        assert 1 not in todo_store["project"]
        assert 2 in todo_store["project"]
        assert todo_store["project"][2].title == "Task 2"

    def test_delete_from_empty_group(self):
        """Should handle deleting from nonexistent group."""
        result = delete_todo.invoke({"task_group": "empty-group", "todo_id": 1})
        
        assert "not found" in result.lower()

    def test_ids_not_reused_after_delete(self):
        """Should not reuse IDs after deletion."""
        create_todo.invoke({"title": "Task 1", "task_group": "project"})
        create_todo.invoke({"title": "Task 2", "task_group": "project"})
        
        delete_todo.invoke({"task_group": "project", "todo_id": 1})
        create_todo.invoke({"title": "Task 3", "task_group": "project"})
        
        # Task 3 should get ID 3, not 1
        assert 3 in todo_store["project"]
        assert todo_store["project"][3].title == "Task 3"


class TestTodoWorkflow:
    """Integration tests for typical todo workflows."""

    def test_complete_workflow(self):
        """Should support a complete create-list-update-delete workflow."""
        # Create todos
        create_todo.invoke({"title": "Step 1: Initialize", "task_group": "workflow"})
        create_todo.invoke({"title": "Step 2: Process", "task_group": "workflow"})
        create_todo.invoke({"title": "Step 3: Finalize", "task_group": "workflow"})
        
        # List todos
        todos = list_todos.invoke({"task_group": "workflow"})
        assert len(todos) == 3
        
        # Update first todo to completed
        update_todo.invoke({"task_group": "workflow", "todo_id": 1, "status": "completed"})
        
        # Verify update
        assert todo_store["workflow"][1].status == "completed"
        assert todo_store["workflow"][2].status == "pending"
        
        # Cancel step 2
        update_todo.invoke({"task_group": "workflow", "todo_id": 2, "status": "cancelled"})
        
        # Complete step 3
        update_todo.invoke({"task_group": "workflow", "todo_id": 3, "status": "completed"})
        
        # Final verification
        assert todo_store["workflow"][1].status == "completed"
        assert todo_store["workflow"][2].status == "cancelled"
        assert todo_store["workflow"][3].status == "completed"

    def test_multiple_projects_workflow(self):
        """Should handle multiple projects independently."""
        # Create todos for two projects
        create_todo.invoke({"title": "Frontend: Build UI", "task_group": "frontend"})
        create_todo.invoke({"title": "Frontend: Style components", "task_group": "frontend"})
        create_todo.invoke({"title": "Backend: Setup API", "task_group": "backend"})
        create_todo.invoke({"title": "Backend: Database schema", "task_group": "backend"})
        
        # Complete frontend task
        update_todo.invoke({"task_group": "frontend", "todo_id": 1, "status": "completed"})
        
        # Verify only frontend is updated
        assert todo_store["frontend"][1].status == "completed"
        assert todo_store["backend"][1].status == "pending"
        
        # List each project
        frontend_todos = list_todos.invoke({"task_group": "frontend"})
        backend_todos = list_todos.invoke({"task_group": "backend"})
        
        assert len(frontend_todos) == 2
        assert len(backend_todos) == 2

    def test_cleanup_workflow(self):
        """Should support cleaning up todos after project completion."""
        # Create and complete todos
        create_todo.invoke({"title": "Task 1", "task_group": "cleanup-test"})
        create_todo.invoke({"title": "Task 2", "task_group": "cleanup-test"})
        
        update_todo.invoke({"task_group": "cleanup-test", "todo_id": 1, "status": "completed"})
        update_todo.invoke({"task_group": "cleanup-test", "todo_id": 2, "status": "completed"})
        
        # Delete all todos
        delete_todo.invoke({"task_group": "cleanup-test", "todo_id": 1})
        delete_todo.invoke({"task_group": "cleanup-test", "todo_id": 2})
        
        # Verify cleanup
        assert len(todo_store["cleanup-test"]) == 0


class TestTodoItemModel:
    """Tests for TodoItem model."""

    def test_todo_item_default_status(self):
        """Should default to pending status."""
        todo = TodoItem(id=1, task_group="test", title="Test")
        assert todo.status == "pending"

    def test_todo_item_valid_statuses(self):
        """Should accept valid status values."""
        pending = TodoItem(id=1, task_group="test", title="Test", status="pending")
        completed = TodoItem(id=2, task_group="test", title="Test", status="completed")
        cancelled = TodoItem(id=3, task_group="test", title="Test", status="cancelled")
        
        assert pending.status == "pending"
        assert completed.status == "completed"
        assert cancelled.status == "cancelled"

    def test_todo_item_has_all_fields(self):
        """Should have all required fields."""
        todo = TodoItem(id=1, task_group="group", title="title", status="pending")
        
        assert hasattr(todo, 'id')
        assert hasattr(todo, 'task_group')
        assert hasattr(todo, 'title')
        assert hasattr(todo, 'status')


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_title(self):
        """Should handle empty title."""
        result = create_todo.invoke({"title": "", "task_group": "group"})
        
        # Should create but with empty title
        assert 1 in todo_store["group"]
        assert todo_store["group"][1].title == ""

    def test_empty_task_group(self):
        """Should handle empty task group."""
        result = create_todo.invoke({"title": "Task", "task_group": ""})
        
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

