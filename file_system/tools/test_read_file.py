import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from file_system.tools.read_file import read_file, ReadFileResult, MAX_LENGTH_OF_LINE
from file_system import settings as settings_module


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files and allow access to it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch settings to allow reading from temp directory
        with patch.object(settings_module.settings, 'present_working_directory', tmpdir):
            yield Path(tmpdir)


@pytest.fixture
def text_file(temp_dir):
    """Create a simple text file."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("line 1\nline 2\nline 3\nline 4\nline 5")
    return str(file_path)


@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file."""
    file_path = temp_dir / "empty.txt"
    file_path.write_text("")
    return str(file_path)


@pytest.fixture
def large_line_file(temp_dir):
    """Create a file with a very long line."""
    file_path = temp_dir / "long_line.txt"
    long_line = "x" * (MAX_LENGTH_OF_LINE + 500)
    file_path.write_text(f"short line\n{long_line}\nanother short line")
    return str(file_path)


@pytest.fixture
def many_lines_file(temp_dir):
    """Create a file with many lines."""
    file_path = temp_dir / "many_lines.txt"
    lines = [f"line {i}" for i in range(100)]
    file_path.write_text("\n".join(lines))
    return str(file_path)


@pytest.fixture
def binary_file(temp_dir):
    """Create a binary file."""
    file_path = temp_dir / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")
    return str(file_path)


class TestReadFileSuccess:
    """Tests for successful file reading."""

    @pytest.mark.asyncio
    async def test_read_simple_text_file(self, text_file):
        """Should read a simple text file successfully."""
        result = await read_file(text_file)
        
        assert result.success is True
        assert result.error is None
        assert "line 1" in result.content
        assert "line 5" in result.content

    @pytest.mark.asyncio
    async def test_read_empty_file(self, empty_file):
        """Should handle empty files."""
        result = await read_file(empty_file)
        
        assert result.success is True
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_read_with_offset(self, many_lines_file):
        """Should skip lines when offset is provided."""
        result = await read_file(many_lines_file, offset=10)
        
        assert result.success is True
        assert "line 10" in result.content
        assert "line 0" not in result.content

    @pytest.mark.asyncio
    async def test_read_with_limit(self, many_lines_file):
        """Should limit number of lines read."""
        result = await read_file(many_lines_file, limit=5)
        
        assert result.success is True
        lines = result.content.split("\n")
        assert len(lines) == 5

    @pytest.mark.asyncio
    async def test_read_with_offset_and_limit(self, many_lines_file):
        """Should handle both offset and limit."""
        result = await read_file(many_lines_file, offset=20, limit=10)
        
        assert result.success is True
        lines = result.content.split("\n")
        assert len(lines) == 10
        assert "line 20" in result.content
        assert "line 29" in result.content


class TestReadFileTruncation:
    """Tests for line truncation behavior."""

    @pytest.mark.asyncio
    async def test_truncate_long_lines(self, large_line_file):
        """Should truncate lines exceeding MAX_LENGTH_OF_LINE."""
        result = await read_file(large_line_file)
        
        assert result.success is True
        lines = result.content.split("\n")
        
        # The long line should be truncated
        long_line = lines[1]
        assert len(long_line) <= MAX_LENGTH_OF_LINE + len("... truncated")
        assert "... truncated" in long_line

    @pytest.mark.asyncio
    async def test_short_lines_not_truncated(self, text_file):
        """Should not truncate short lines."""
        result = await read_file(text_file)
        
        assert result.success is True
        assert "... truncated" not in result.content


class TestReadFileErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_file_not_found(self, temp_dir):
        """Should return error when file doesn't exist."""
        result = await read_file(str(temp_dir / "nonexistent.txt"))
        
        assert isinstance(result, ReadFileResult)
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_path_is_directory(self, temp_dir):
        """Should return error when path is a directory."""
        result = await read_file(str(temp_dir))
        
        assert isinstance(result, ReadFileResult)
        assert result.success is False
        assert "directory" in result.error

    @pytest.mark.asyncio
    async def test_binary_file_rejected(self, binary_file):
        """Should reject binary files."""
        result = await read_file(binary_file)
        
        assert isinstance(result, ReadFileResult)
        assert result.success is False
        assert "text content" in result.error


class TestReadFileEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_offset_beyond_file_length(self, text_file):
        """Should handle offset beyond file length gracefully."""
        result = await read_file(text_file, offset=1000)
        
        assert result.success is True
        # Should return the last line or empty
        lines = result.content.split("\n")
        assert len(lines) <= 1

    @pytest.mark.asyncio
    async def test_zero_limit(self, text_file):
        """Should return empty content with zero limit."""
        result = await read_file(text_file, limit=0)
        
        assert result.success is True
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_negative_offset_treated_as_zero(self, text_file):
        """Should treat negative offset as zero."""
        result = await read_file(text_file, offset=-10)
        
        assert result.success is True
        assert "line 1" in result.content

    @pytest.mark.asyncio
    async def test_file_with_unicode(self, temp_dir):
        """Should handle files with unicode content."""
        file_path = temp_dir / "unicode.txt"
        file_path.write_text("Hello 世界\nПривет мир\n🚀 emoji", encoding="utf-8")
        
        result = await read_file(str(file_path))
        
        assert result.success is True
        assert "世界" in result.content
        assert "Привет" in result.content
        assert "🚀" in result.content

    @pytest.mark.asyncio
    async def test_file_with_special_characters(self, temp_dir):
        """Should handle files with special characters in content."""
        file_path = temp_dir / "special.txt"
        file_path.write_text("tab\there\nnewline above\r\nwindows line")
        
        result = await read_file(str(file_path))
        
        assert result.success is True
        assert "tab\there" in result.content

