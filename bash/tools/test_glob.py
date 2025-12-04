import pytest
import tempfile
from pathlib import Path

from bash.tools.glob import glob
from base.models import GlobToolResult
from base.settings import settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files within the allowed test directory."""
    # Create temp dir within settings.present_test_directory so it passes validation
    test_base = Path(settings.present_test_directory)
    test_base.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory(dir=str(test_base)) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def populated_temp_dir(temp_dir):
    """Create a temp directory with various files for testing."""
    # Create files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    (temp_dir / "script.py").write_text("print('hello')")
    (temp_dir / "data.json").write_text("{}")
    
    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested content")
    (subdir / "nested.py").write_text("# nested python")
    
    # Create another subdirectory
    subdir2 = temp_dir / "another"
    subdir2.mkdir()
    (subdir2 / "deep.txt").write_text("deep content")
    
    yield temp_dir


class TestGlobBasicPatterns:
    """Tests for basic glob pattern matching."""

    @pytest.mark.asyncio
    async def test_match_all_txt_files(self, populated_temp_dir):
        """Should match all .txt files in directory."""
        result = await glob("*.txt", str(populated_temp_dir))
        
        assert result.success is True
        assert isinstance(result, GlobToolResult)
        assert len(result.files) == 2
        assert any("file1.txt" in f for f in result.files)
        assert any("file2.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_match_all_py_files(self, populated_temp_dir):
        """Should match all .py files in directory."""
        result = await glob("*.py", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 1
        assert any("script.py" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_match_specific_file(self, populated_temp_dir):
        """Should match a specific file by name."""
        result = await glob("data.json", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 1
        assert any("data.json" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_match_all_files(self, populated_temp_dir):
        """Should match all files with wildcard."""
        result = await glob("*", str(populated_temp_dir))
        
        assert result.success is True
        # Should include files and directories
        assert len(result.files) >= 4  # At least file1.txt, file2.txt, script.py, data.json

    @pytest.mark.asyncio
    async def test_no_matches(self, populated_temp_dir):
        """Should return empty list when no files match."""
        result = await glob("*.xyz", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 0


class TestGlobRecursivePatterns:
    """Tests for recursive glob patterns."""

    @pytest.mark.asyncio
    async def test_recursive_txt_files(self, populated_temp_dir):
        """Should match all .txt files recursively."""
        result = await glob("**/*.txt", str(populated_temp_dir))
        
        assert result.success is True
        # Should find: file1.txt, file2.txt, subdir/nested.txt, another/deep.txt
        assert len(result.files) == 4
        assert any("nested.txt" in f for f in result.files)
        assert any("deep.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_recursive_py_files(self, populated_temp_dir):
        """Should match all .py files recursively."""
        result = await glob("**/*.py", str(populated_temp_dir))
        
        assert result.success is True
        # Should find: script.py, subdir/nested.py
        assert len(result.files) == 2
        assert any("script.py" in f for f in result.files)
        assert any("nested.py" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_recursive_all_files(self, populated_temp_dir):
        """Should match all files recursively."""
        result = await glob("**/*", str(populated_temp_dir))
        
        assert result.success is True
        # Should find all files and directories
        assert len(result.files) >= 6


class TestGlobDirectoryPatterns:
    """Tests for directory-specific patterns."""

    @pytest.mark.asyncio
    async def test_files_in_subdirectory(self, populated_temp_dir):
        """Should match files in a specific subdirectory."""
        result = await glob("subdir/*", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 2
        assert any("nested.txt" in f for f in result.files)
        assert any("nested.py" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_specific_extension_in_subdirectory(self, populated_temp_dir):
        """Should match specific extension in subdirectory."""
        result = await glob("subdir/*.txt", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 1
        assert any("nested.txt" in f for f in result.files)


class TestGlobDirectoryValidation:
    """Tests for directory validation."""

    @pytest.mark.asyncio
    async def test_nonexistent_directory(self):
        """Should fail for non-existent directory."""
        result = await glob("*.txt", "/nonexistent_directory_xyz")
        
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_file_as_directory(self, populated_temp_dir):
        """Should fail when path is a file, not a directory."""
        file_path = str(populated_temp_dir / "file1.txt")
        result = await glob("*.txt", file_path)
        
        assert result.success is False
        assert "not a directory" in result.error

    @pytest.mark.asyncio
    async def test_path_outside_test_directory(self, temp_dir):
        """Should fail when path is outside the allowed test directory."""
        result = await glob("*.txt", "/tmp")
        
        assert result.success is False
        assert "not in the present working directory" in result.error


class TestGlobResultStructure:
    """Tests for result structure and properties."""

    @pytest.mark.asyncio
    async def test_result_type(self, populated_temp_dir):
        """Should return correct result type."""
        result = await glob("*.txt", str(populated_temp_dir))
        
        assert isinstance(result, GlobToolResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'error')
        assert hasattr(result, 'files')

    @pytest.mark.asyncio
    async def test_files_are_strings(self, populated_temp_dir):
        """Should return files as list of strings."""
        result = await glob("*.txt", str(populated_temp_dir))
        
        assert isinstance(result.files, list)
        for file in result.files:
            assert isinstance(file, str)

    @pytest.mark.asyncio
    async def test_files_are_absolute_paths(self, populated_temp_dir):
        """Should return absolute file paths."""
        result = await glob("*.txt", str(populated_temp_dir))
        
        assert result.success is True
        for file in result.files:
            assert Path(file).is_absolute()

    @pytest.mark.asyncio
    async def test_files_sorted_by_mtime(self, populated_temp_dir):
        """Should return files sorted by modification time (newest first)."""
        import time
        
        # Create files with different modification times
        file_old = populated_temp_dir / "old.txt"
        file_old.write_text("old")
        time.sleep(0.1)
        
        file_new = populated_temp_dir / "new.txt"
        file_new.write_text("new")
        
        result = await glob("*.txt", str(populated_temp_dir))
        
        assert result.success is True
        # Find indices of our test files
        txt_files = [f for f in result.files if "old.txt" in f or "new.txt" in f]
        if len(txt_files) >= 2:
            # new.txt should appear before old.txt (newest first)
            new_idx = next(i for i, f in enumerate(result.files) if "new.txt" in f)
            old_idx = next(i for i, f in enumerate(result.files) if "old.txt" in f)
            assert new_idx < old_idx


class TestGlobEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_directory(self, temp_dir):
        """Should handle empty directory."""
        result = await glob("*.txt", str(temp_dir))
        
        assert result.success is True
        assert len(result.files) == 0

    @pytest.mark.asyncio
    async def test_hidden_files(self, temp_dir):
        """Should handle hidden files."""
        hidden_file = temp_dir / ".hidden.txt"
        hidden_file.write_text("hidden")
        
        result = await glob(".*", str(temp_dir))
        
        assert result.success is True
        assert any(".hidden.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_special_characters_in_filename(self, temp_dir):
        """Should handle files with special characters."""
        special_file = temp_dir / "file with spaces.txt"
        special_file.write_text("special")
        
        result = await glob("*.txt", str(temp_dir))
        
        assert result.success is True
        assert any("file with spaces.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_unicode_filename(self, temp_dir):
        """Should handle unicode filenames."""
        unicode_file = temp_dir / "文件.txt"
        unicode_file.write_text("unicode content")
        
        result = await glob("*.txt", str(temp_dir))
        
        assert result.success is True
        assert any("文件.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_question_mark_pattern(self, populated_temp_dir):
        """Should handle ? wildcard pattern."""
        result = await glob("file?.txt", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 2
        assert any("file1.txt" in f for f in result.files)
        assert any("file2.txt" in f for f in result.files)

    @pytest.mark.asyncio
    async def test_character_class_pattern(self, populated_temp_dir):
        """Should handle character class pattern."""
        result = await glob("file[12].txt", str(populated_temp_dir))
        
        assert result.success is True
        assert len(result.files) == 2

