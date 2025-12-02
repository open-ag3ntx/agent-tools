import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from command_line.tools.execute_command import (
    execute_command,
    is_command_blocked,
    is_command_dangerous,
    is_directory_allowed,
)
from command_line.models import CommandResult
from command_line import settings as settings_module


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch settings to allow the temp directory
        with patch.object(settings_module.settings, 'present_working_directory', tmpdir):
            with patch.object(settings_module.settings, 'allowed_directories', [tmpdir, '/tmp']):
                with patch.object(settings_module.settings, 'working_directory', tmpdir):
                    yield Path(tmpdir)


class TestExecuteCommandSuccess:
    """Tests for successful command execution."""

    @pytest.mark.asyncio
    async def test_simple_command(self, temp_dir):
        """Should execute a simple command successfully."""
        result = await execute_command("echo 'Hello, World!'", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "Hello, World!" in result.stdout
        assert result.return_code == 0

    @pytest.mark.asyncio
    async def test_ls_command(self, temp_dir):
        """Should execute ls command."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        result = await execute_command("ls", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "test.txt" in result.stdout

    @pytest.mark.asyncio
    async def test_pwd_command(self, temp_dir):
        """Should execute pwd in the correct directory."""
        result = await execute_command("pwd", working_directory=str(temp_dir))
        
        assert result.success is True
        assert str(temp_dir) in result.stdout

    @pytest.mark.asyncio
    async def test_cat_command(self, temp_dir):
        """Should read file content with cat."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("file content here")
        
        result = await execute_command("cat test.txt", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "file content here" in result.stdout

    @pytest.mark.asyncio
    async def test_command_with_pipe(self, temp_dir):
        """Should handle piped commands."""
        result = await execute_command("echo 'line1\nline2\nline3' | wc -l", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "3" in result.stdout

    @pytest.mark.asyncio
    async def test_command_creates_file(self, temp_dir):
        """Should create files via commands."""
        result = await execute_command("touch new_file.txt", working_directory=str(temp_dir))
        
        assert result.success is True
        assert (temp_dir / "new_file.txt").exists()

    @pytest.mark.asyncio
    async def test_python_command(self, temp_dir):
        """Should execute Python commands."""
        result = await execute_command("python3 -c 'print(1 + 1)'", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "2" in result.stdout


class TestExecuteCommandErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_command_not_found(self, temp_dir):
        """Should handle command not found."""
        result = await execute_command("nonexistent_command_xyz", working_directory=str(temp_dir))
        
        assert result.success is False
        assert result.return_code != 0

    @pytest.mark.asyncio
    async def test_command_fails(self, temp_dir):
        """Should handle command failure."""
        result = await execute_command("ls /nonexistent_directory_xyz", working_directory=str(temp_dir))
        
        assert result.success is False
        assert result.stderr is not None

    @pytest.mark.asyncio
    async def test_invalid_working_directory(self, temp_dir):
        """Should fail for non-existent working directory."""
        result = await execute_command("echo test", working_directory="/nonexistent/path")
        
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_file_as_working_directory(self, temp_dir):
        """Should fail when working directory is a file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        result = await execute_command("echo test", working_directory=str(test_file))
        
        assert result.success is False
        assert "not a directory" in result.error


class TestCommandBlocking:
    """Tests for command security features."""

    def test_blocked_command_detection(self):
        """Should detect blocked commands."""
        assert is_command_blocked("rm -rf /") is True
        assert is_command_blocked("rm -rf /*") is True
        assert is_command_blocked("echo hello") is False

    def test_dangerous_pattern_detection(self):
        """Should detect dangerous patterns."""
        assert is_command_dangerous("sudo apt install") == "sudo"
        assert is_command_dangerous("rm -rf ./node_modules") == "rm -rf"
        assert is_command_dangerous("echo hello") is None

    @pytest.mark.asyncio
    async def test_blocked_command_rejected(self, temp_dir):
        """Should reject blocked commands."""
        result = await execute_command("rm -rf /", working_directory=str(temp_dir))
        
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_dangerous_command_warns(self, temp_dir):
        """Should warn but allow dangerous commands."""
        # Use chmod 777 which is dangerous but not blocked
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        result = await execute_command(f"chmod 777 {test_file}", working_directory=str(temp_dir))
        
        # Should execute but with warning in stderr
        assert result.success is True
        assert "Warning" in (result.stderr or "")


class TestDirectoryRestrictions:
    """Tests for directory restrictions."""

    def test_allowed_directory_check(self, temp_dir):
        """Should check directory allowlist."""
        with patch.object(settings_module.settings, 'present_working_directory', str(temp_dir)):
            with patch.object(settings_module.settings, 'allowed_directories', [str(temp_dir)]):
                assert is_directory_allowed(str(temp_dir)) is True
                assert is_directory_allowed("/some/other/path") is False

    @pytest.mark.asyncio
    async def test_disallowed_directory_rejected(self):
        """Should reject commands in disallowed directories."""
        with patch.object(settings_module.settings, 'present_working_directory', '/tmp'):
            with patch.object(settings_module.settings, 'allowed_directories', ['/tmp']):
                result = await execute_command("echo test", working_directory="/var/log")
                
                assert result.success is False
                assert "not allowed" in result.error


class TestTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_command_timeout(self, temp_dir):
        """Should timeout long-running commands."""
        result = await execute_command("sleep 10", working_directory=str(temp_dir), timeout=1)
        
        assert result.success is False
        assert result.timed_out is True
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_custom_timeout(self, temp_dir):
        """Should respect custom timeout."""
        result = await execute_command("sleep 1", working_directory=str(temp_dir), timeout=5)
        
        assert result.success is True
        assert result.timed_out is False


class TestCommandResult:
    """Tests for CommandResult structure."""

    @pytest.mark.asyncio
    async def test_result_contains_all_fields(self, temp_dir):
        """Should return complete result structure."""
        result = await execute_command("echo test", working_directory=str(temp_dir))
        
        assert isinstance(result, CommandResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'stdout')
        assert hasattr(result, 'stderr')
        assert hasattr(result, 'return_code')
        assert hasattr(result, 'command')
        assert hasattr(result, 'working_directory')
        assert hasattr(result, 'timed_out')

    @pytest.mark.asyncio
    async def test_result_contains_command(self, temp_dir):
        """Should include the executed command in result."""
        result = await execute_command("echo hello", working_directory=str(temp_dir))
        
        assert result.command == "echo hello"

    @pytest.mark.asyncio
    async def test_result_contains_working_directory(self, temp_dir):
        """Should include the working directory in result."""
        result = await execute_command("pwd", working_directory=str(temp_dir))
        
        assert result.working_directory == str(temp_dir)


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_command(self, temp_dir):
        """Should handle empty command."""
        result = await execute_command("", working_directory=str(temp_dir))
        
        # Empty command should either fail or return empty output
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_command_with_special_characters(self, temp_dir):
        """Should handle special characters in command."""
        result = await execute_command("echo 'hello $USER'", working_directory=str(temp_dir))
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_command_with_newlines(self, temp_dir):
        """Should handle commands with newlines in output."""
        result = await execute_command("echo -e 'line1\\nline2\\nline3'", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "\n" in result.stdout or "line1" in result.stdout

    @pytest.mark.asyncio
    async def test_unicode_output(self, temp_dir):
        """Should handle unicode in output."""
        result = await execute_command("echo '你好世界 🌍'", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "你好世界" in result.stdout or "🌍" in result.stdout

    @pytest.mark.asyncio
    async def test_large_output(self, temp_dir):
        """Should handle large output."""
        result = await execute_command("seq 1 1000", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "1000" in result.stdout

