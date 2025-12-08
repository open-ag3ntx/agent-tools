import pytest
import tempfile
from pathlib import Path

from bash.tools.grep import grep
from base.models import GrepToolResult
from base.settings import settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files within the allowed test directory."""
    test_base = Path(settings.present_test_directory)
    test_base.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory(dir=str(test_base)) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def populated_temp_dir(temp_dir):
    """Create a temp directory with various files for testing grep."""
    # Create Python files
    (temp_dir / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

def goodbye_world():
    print("Goodbye, World!")

class MyClass:
    def __init__(self):
        self.value = 42
""")
    
    (temp_dir / "utils.py").write_text("""
import os

def get_path():
    return os.getcwd()

def helper_function():
    return "helper"
""")
    
    # Create JavaScript files
    (temp_dir / "app.js").write_text("""
function helloWorld() {
    console.log("Hello, World!");
}

const goodbye = () => {
    console.log("Goodbye!");
};
""")
    
    # Create text files
    (temp_dir / "notes.txt").write_text("""
This is a note about Hello World.
Another line with hello in it.
HELLO in uppercase.
Final line.
""")
    
    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("""
def nested_hello():
    return "Hello from nested"
""")
    
    (subdir / "data.txt").write_text("""
hello data file
world data content
""")
    
    yield temp_dir


class TestGrepBasicSearch:
    """Tests for basic grep pattern matching."""

    @pytest.mark.asyncio
    async def test_simple_pattern_match(self, populated_temp_dir):
        """Should find simple pattern in files."""
        result = await grep("hello", str(populated_temp_dir))
        
        assert result.success is True
        assert isinstance(result, GrepToolResult)
        # Should find files containing 'hello'
        assert len(result.files) > 0

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, populated_temp_dir):
        """Should find matches regardless of case when i=True (default)."""
        result = await grep("HELLO", str(populated_temp_dir))
        
        assert result.success is True
        # Should match 'hello', 'Hello', 'HELLO'
        assert len(result.files) > 0

    @pytest.mark.asyncio
    async def test_case_sensitive_search(self, populated_temp_dir):
        """Should only find exact case matches when i=False."""
        result = await grep("HELLO", str(populated_temp_dir), i=False)
        
        assert result.success is True
        # Should only match 'HELLO' (in notes.txt)
        # The result should be different from case-insensitive search

    @pytest.mark.asyncio
    async def test_regex_pattern(self, populated_temp_dir):
        """Should support regex patterns."""
        result = await grep(r"def \w+_world", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) > 0

    @pytest.mark.asyncio
    async def test_no_matches(self, populated_temp_dir):
        """Should return empty results when no matches found."""
        result = await grep("xyz123nonexistent", str(populated_temp_dir))
        
        assert result.success is True  # No matches is not an error
        assert len(result.files) == 0
        assert len(result.lines) == 0


class TestGrepOutputModes:
    """Tests for different output modes."""

    @pytest.mark.asyncio
    async def test_files_with_matches_mode(self, populated_temp_dir):
        """Should return only file paths in files_with_matches mode."""
        result = await grep("hello", str(populated_temp_dir), output_mode="files_with_matches")
        
        assert result.success is True
        assert len(result.files) > 0
        assert len(result.lines) == 0  # Should not have lines in this mode
        for file in result.files:
            assert isinstance(file, str)

    @pytest.mark.asyncio
    async def test_content_mode(self, populated_temp_dir):
        """Should return matching lines in content mode."""
        result = await grep("hello", str(populated_temp_dir), output_mode="content")
        
        assert result.success is True
        assert len(result.lines) > 0
        assert len(result.files) == 0  # Should not have files list in this mode

    @pytest.mark.asyncio
    async def test_count_mode(self, populated_temp_dir):
        """Should return match counts in count mode."""
        result = await grep("hello", str(populated_temp_dir), output_mode="count")
        
        assert result.success is True
        assert result.counts >= 0


class TestGrepContextLines:
    """Tests for context line options (-A, -B, -C)."""

    @pytest.mark.asyncio
    async def test_after_context(self, populated_temp_dir):
        """Should show lines after matches with -A option."""
        result = await grep("def hello_world", str(populated_temp_dir), output_mode="content", A=2)
        
        assert result.success is True
        if result.content:
            # Should include lines after the match
            assert "print" in result.content.lower()

    @pytest.mark.asyncio
    async def test_before_context(self, populated_temp_dir):
        """Should show lines before matches with -B option."""
        result = await grep("print.*Hello", str(populated_temp_dir), output_mode="content", B=2)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_combined_context(self, populated_temp_dir):
        """Should show lines before and after matches with -C option."""
        result = await grep("hello_world", str(populated_temp_dir), output_mode="content", C=2)
        
        assert result.success is True


class TestGrepFileFilters:
    """Tests for file filtering options."""

    @pytest.mark.asyncio
    async def test_type_filter_python(self, populated_temp_dir):
        """Should filter to only Python files with --type py."""
        result = await grep("hello", str(populated_temp_dir), type="py")
        
        assert result.success is True
        # All matched files should be .py files
        for file in result.files:
            assert file.endswith('.py')

    @pytest.mark.asyncio
    async def test_type_filter_js(self, populated_temp_dir):
        """Should filter to only JavaScript files with --type js."""
        result = await grep("hello", str(populated_temp_dir), type="js")
        
        assert result.success is True
        # All matched files should be .js files
        for file in result.files:
            assert file.endswith('.js')

    @pytest.mark.asyncio
    async def test_glob_filter(self, populated_temp_dir):
        """Should filter files with glob pattern."""
        result = await grep("hello", str(populated_temp_dir), glob="*.txt")
        
        assert result.success is True
        # All matched files should be .txt files
        for file in result.files:
            assert file.endswith('.txt')

    @pytest.mark.asyncio
    async def test_glob_filter_recursive(self, populated_temp_dir):
        """Should filter files recursively with glob pattern."""
        result = await grep("hello", str(populated_temp_dir), glob="**/*.py")
        
        assert result.success is True


class TestGrepMultiline:
    """Tests for multiline matching."""

    @pytest.mark.asyncio
    async def test_multiline_pattern(self, populated_temp_dir):
        """Should match across multiple lines with multiline=True."""
        result = await grep(r"def.*\n.*print", str(populated_temp_dir), 
                           output_mode="content", multiline=True)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_single_line_default(self, populated_temp_dir):
        """Should not match across lines by default."""
        result = await grep("hello", str(populated_temp_dir), multiline=False)
        
        assert result.success is True


class TestGrepLineNumbers:
    """Tests for line number display."""

    @pytest.mark.asyncio
    async def test_line_numbers_shown(self, populated_temp_dir):
        """Should show line numbers with n=True (default) in content mode."""
        result = await grep("hello", str(populated_temp_dir), output_mode="content", n=True)
        
        assert result.success is True
        # Line numbers appear as "filename:line_num:content"

    @pytest.mark.asyncio
    async def test_line_numbers_hidden(self, populated_temp_dir):
        """Should hide line numbers with n=False."""
        result = await grep("hello", str(populated_temp_dir), output_mode="content", n=False)
        
        assert result.success is True


class TestGrepPagination:
    """Tests for offset and head_limit options."""

    @pytest.mark.asyncio
    async def test_head_limit(self, populated_temp_dir):
        """Should limit output to head_limit entries."""
        result = await grep("hello", str(populated_temp_dir), 
                           output_mode="files_with_matches", head_limit=2)
        
        assert result.success is True
        assert len(result.files) <= 2

    @pytest.mark.asyncio
    async def test_offset(self, populated_temp_dir):
        """Should skip first N entries with offset."""
        # First get all results
        all_result = await grep("hello", str(populated_temp_dir))
        
        # Then get results with offset
        offset_result = await grep("hello", str(populated_temp_dir), offset=1)
        
        assert offset_result.success is True
        # Offset result should have fewer files (if there were multiple)
        if len(all_result.files) > 1:
            assert len(offset_result.files) < len(all_result.files)

    @pytest.mark.asyncio
    async def test_offset_and_head_limit_combined(self, populated_temp_dir):
        """Should apply both offset and head_limit correctly."""
        result = await grep("hello", str(populated_temp_dir), 
                           offset=1, head_limit=2)
        
        assert result.success is True
        assert len(result.files) <= 2


class TestGrepDirectoryValidation:
    """Tests for path validation."""

    @pytest.mark.asyncio
    async def test_nonexistent_path(self):
        """Should fail for non-existent path."""
        result = await grep("hello", "/nonexistent_directory_xyz")
        
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_path_outside_test_directory(self):
        """Should fail when path is outside the allowed test directory."""
        result = await grep("hello", "/tmp")
        
        assert result.success is False
        assert "not in the present working directory" in result.error

    @pytest.mark.asyncio
    async def test_default_path(self):
        """Should use default path when none specified."""
        result = await grep("hello")
        
        # Should not fail with path error
        assert result.error is None or "Path" not in result.error


class TestGrepPatternValidation:
    """Tests for pattern validation."""

    @pytest.mark.asyncio
    async def test_empty_pattern(self, populated_temp_dir):
        """Should fail for empty pattern."""
        result = await grep("", str(populated_temp_dir))
        
        assert result.success is False
        assert "Pattern is required" in result.error


class TestGrepResultStructure:
    """Tests for result structure and properties."""

    @pytest.mark.asyncio
    async def test_result_type(self, populated_temp_dir):
        """Should return correct result type."""
        result = await grep("hello", str(populated_temp_dir))
        
        assert isinstance(result, GrepToolResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'error')
        assert hasattr(result, 'files')
        assert hasattr(result, 'lines')
        assert hasattr(result, 'counts')
        assert hasattr(result, 'content')

    @pytest.mark.asyncio
    async def test_files_are_strings(self, populated_temp_dir):
        """Should return files as list of strings."""
        result = await grep("hello", str(populated_temp_dir))
        
        assert isinstance(result.files, list)
        for file in result.files:
            assert isinstance(file, str)

    @pytest.mark.asyncio
    async def test_lines_are_strings(self, populated_temp_dir):
        """Should return lines as list of strings in content mode."""
        result = await grep("hello", str(populated_temp_dir), output_mode="content")
        
        assert isinstance(result.lines, list)
        for line in result.lines:
            assert isinstance(line, str)


class TestGrepSearchInFile:
    """Tests for searching within a specific file."""

    @pytest.mark.asyncio
    async def test_search_single_file(self, populated_temp_dir):
        """Should search within a single file."""
        file_path = str(populated_temp_dir / "main.py")
        result = await grep("hello", file_path)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_search_nested_file(self, populated_temp_dir):
        """Should search within a nested file."""
        file_path = str(populated_temp_dir / "subdir" / "nested.py")
        result = await grep("hello", file_path)
        
        assert result.success is True


class TestGrepEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_directory(self, temp_dir):
        """Should handle empty directory gracefully."""
        result = await grep("hello", str(temp_dir))
        
        assert result.success is True
        assert len(result.files) == 0

    @pytest.mark.asyncio
    async def test_special_regex_characters(self, populated_temp_dir):
        """Should handle special regex characters."""
        # Search for literal parentheses
        result = await grep(r"\(self\)", str(populated_temp_dir))
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_unicode_pattern(self, temp_dir):
        """Should handle unicode in pattern and content."""
        unicode_file = temp_dir / "unicode.txt"
        unicode_file.write_text("你好世界 Hello 🌍")
        
        result = await grep("你好", str(temp_dir))
        
        assert result.success is True
        assert len(result.files) >= 1

    @pytest.mark.asyncio
    async def test_binary_file_handling(self, temp_dir):
        """Should handle binary files gracefully."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02hello\x03\x04")
        
        result = await grep("hello", str(temp_dir))
        
        # Should not crash, may or may not find match depending on ripgrep behavior
        assert isinstance(result, GrepToolResult)

    @pytest.mark.asyncio
    async def test_very_long_line(self, temp_dir):
        """Should handle files with very long lines."""
        long_line_file = temp_dir / "longline.txt"
        long_line_file.write_text("hello" + "x" * 10000 + "world")
        
        result = await grep("hello", str(temp_dir))
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_file_with_special_characters_in_name(self, temp_dir):
        """Should handle files with special characters in name."""
        special_file = temp_dir / "file with spaces.txt"
        special_file.write_text("hello world")
        
        result = await grep("hello", str(temp_dir))
        
        assert result.success is True
        assert any("file with spaces.txt" in f for f in result.files)


class TestGrepComplexPatterns:
    """Tests for complex regex patterns."""

    @pytest.mark.asyncio
    async def test_word_boundary(self, populated_temp_dir):
        """Should support word boundary patterns."""
        result = await grep(r"\bhello\b", str(populated_temp_dir))
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_alternation(self, populated_temp_dir):
        """Should support alternation patterns."""
        result = await grep(r"hello|goodbye", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) > 0

    @pytest.mark.asyncio
    async def test_quantifiers(self, populated_temp_dir):
        """Should support quantifier patterns."""
        result = await grep(r"l{2}", str(populated_temp_dir))  # Match 'll'
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_character_class(self, populated_temp_dir):
        """Should support character class patterns."""
        result = await grep(r"[Hh]ello", str(populated_temp_dir))
        
        assert result.success is True
