import pytest
import tempfile
from pathlib import Path

from base import bash_utils
from bash.tools.bash import bash
from base.models import CommandResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestExecuteCommandSuccess:
    """Tests for successful command execution."""

    @pytest.mark.asyncio
    async def test_simple_command(self, temp_dir):
        """Should execute a simple command successfully."""
        result = await bash("echo 'Hello, World!'", description="Test simple command", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "Hello, World!" in result.stdout
        assert result.return_code == 0

    @pytest.mark.asyncio
    async def test_ls_command(self, temp_dir):
        """Should execute ls command."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        result = await bash("ls", description="Test ls command", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "test.txt" in result.stdout

    @pytest.mark.asyncio
    async def test_pwd_command(self, temp_dir):
        """Should execute pwd in the correct directory."""
        result = await bash("pwd", description="Test pwd command", working_directory=str(temp_dir))
        
        assert result.success is True
        assert str(temp_dir) in result.stdout

    @pytest.mark.asyncio
    async def test_cat_command(self, temp_dir):
        """Should read file content with cat."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("file content here")
        
        result = await bash("cat test.txt", description="Test cat command", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "file content here" in result.stdout

    @pytest.mark.asyncio
    async def test_command_with_pipe(self, temp_dir):
        """Should handle piped commands."""
        result = await bash("echo 'line1\nline2\nline3' | wc -l", description="Test command with pipe", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "3" in result.stdout

    @pytest.mark.asyncio
    async def test_command_creates_file(self, temp_dir):
        """Should create files via commands."""
        result = await bash("touch new_file.txt", description="Test command creates file", working_directory=str(temp_dir))
        
        assert result.success is True
        assert (temp_dir / "new_file.txt").exists()

    @pytest.mark.asyncio
    async def test_python_command(self, temp_dir):
        """Should execute Python commands."""
        result = await bash("python3 -c 'print(1 + 1)'", description="Test python command", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "2" in result.stdout


class TestExecuteCommandErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_command_not_found(self, temp_dir):
        """Should handle command not found."""
        result = await bash("nonexistent_command_xyz", description="Test command not found", working_directory=str(temp_dir))
        
        assert result.success is False
        assert result.return_code != 0

    @pytest.mark.asyncio
    async def test_command_fails(self, temp_dir):
        """Should handle command failure."""
        result = await bash("ls /nonexistent_directory_xyz", description="Test command fails", working_directory=str(temp_dir))
        
        assert result.success is False
        assert result.stderr is not None

    @pytest.mark.asyncio
    async def test_invalid_working_directory(self):
        """Should fail for non-existent working directory."""
        result = await bash("echo test", description="Test invalid working directory", working_directory="/nonexistent_directory_xyz")
        
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_file_as_working_directory(self, temp_dir):
        """Should fail when working directory is a file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        result = await bash("echo test", description="Test file as working directory", working_directory=str(test_file))
        
        assert result.success is False
        assert "not a directory" in result.error


class TestCommandBlocking:
    """Tests for command security features."""

    def test_blocked_command_detection(self):
        """Should detect blocked commands."""
        assert bash_utils.is_command_blocked("rm -rf /") is True
        assert bash_utils.is_command_blocked("rm -rf /*") is True
        assert bash_utils.is_command_blocked("echo hello") is False

    def test_dangerous_pattern_detection(self):
        """Should detect dangerous patterns."""
        assert bash_utils.is_command_dangerous("sudo apt install") == "sudo"
        assert bash_utils.is_command_dangerous("rm -rf ./node_modules") == "rm -rf"
        assert bash_utils.is_command_dangerous("echo hello") is None

    @pytest.mark.asyncio
    async def test_blocked_command_rejected(self, temp_dir):
        """Should reject blocked commands."""
        result = await bash("rm -rf /", description="Test blocked command", working_directory=str(temp_dir))
        
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_dangerous_command_rejected(self, temp_dir):
        """Should reject dangerous commands."""
        # Use chmod 777 which is dangerous
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        result = await bash(f"chmod 777 {test_file}", description="Test dangerous command", working_directory=str(temp_dir))
        
        # Should fail with error about dangerous pattern
        assert result.success is False
        assert "dangerous" in result.error.lower()


class TestDirectoryRestrictions:
    """Tests for directory restrictions."""

    def test_blocked_command_patterns(self):
        """Should detect blocked command patterns."""
        assert bash_utils.is_command_blocked("rm -rf /") is True
        assert bash_utils.is_command_blocked("rm -rf /*") is True
        assert bash_utils.is_command_blocked("mkfs.ext4 /dev/sda") is True
        assert bash_utils.is_command_blocked("echo hello") is False

    def test_dangerous_command_patterns(self):
        """Should detect dangerous command patterns."""
        assert bash_utils.is_command_dangerous("sudo apt install") == "sudo"
        assert bash_utils.is_command_dangerous("chmod 777 file.txt") == "chmod 777"
        assert bash_utils.is_command_dangerous("echo hello") is None


class TestTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_command_timeout(self, temp_dir):
        """Should timeout long-running commands."""
        # Use a Python one-liner that sleeps
        result = await bash("python3 -c 'import time; time.sleep(10)'", description="Test command timeout", timeout=1, working_directory=str(temp_dir))
        
        assert result.success is False
        assert result.timed_out is True
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_custom_timeout(self, temp_dir):
        """Should respect custom timeout."""
        result = await bash("python3 -c 'import time; time.sleep(0.5)'", description="Test custom timeout", timeout=5, working_directory=str(temp_dir))
        
        assert result.success is True
        assert result.timed_out is False


class TestCommandResult:
    """Tests for CommandResult structure."""

    @pytest.mark.asyncio
    async def test_result_contains_all_fields(self, temp_dir):
        """Should return complete result structure."""
        result = await bash("echo test", description="Test result contains all fields", working_directory=str(temp_dir))
        
        assert isinstance(result, CommandResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'stdout')
        assert hasattr(result, 'stderr')
        assert hasattr(result, 'return_code')
        assert hasattr(result, 'command')
        assert hasattr(result, 'timed_out')

    @pytest.mark.asyncio
    async def test_result_contains_command(self, temp_dir):
        """Should include the executed command in result."""
        result = await bash("echo hello", description="Test result contains command", working_directory=str(temp_dir))
        
        assert result.command == "echo hello"

    @pytest.mark.asyncio
    async def test_result_contains_run_in_background(self, temp_dir):
        """Should include run_in_background in result."""
        result = await bash("pwd", description="Test result contains run_in_background", working_directory=str(temp_dir))
        
        assert hasattr(result, 'run_in_background')
        assert result.run_in_background is False


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_command(self, temp_dir):
        """Should handle empty command."""
        result = await bash("", description="Test empty command", working_directory=str(temp_dir))
        
        # Empty command should either fail or return empty output
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_command_with_special_characters(self, temp_dir):
        """Should handle special characters in command."""
        result = await bash("echo 'hello $USER'", description="Test command with special characters", working_directory=str(temp_dir))
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_command_with_newlines(self, temp_dir):
        """Should handle commands with newlines in output."""
        result = await bash("echo -e 'line1\\nline2\\nline3'", description="Test command with newlines", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "\n" in result.stdout or "line1" in result.stdout

    @pytest.mark.asyncio
    async def test_unicode_output(self, temp_dir):
        """Should handle unicode in output."""
        result = await bash("echo '你好世界 🌍'", description="Test command with unicode", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "你好世界" in result.stdout or "🌍" in result.stdout

    @pytest.mark.asyncio
    async def test_large_output(self, temp_dir):
        """Should handle large output."""
        result = await bash("seq 1 1000", description="Test large output", working_directory=str(temp_dir))
        
        assert result.success is True
        assert "1000" in result.stdout

