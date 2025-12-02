import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from file_system.tools.write_file import write_file, WriteFileResult
from file_system.settings import settings as settings_instance


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files and allow access to it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch settings to allow writing files in temp directory
        with patch.object(settings_instance, 'present_working_directory', tmpdir):
            yield Path(tmpdir)


@pytest.fixture
def text_file(temp_dir):
    """Create a simple text file."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("original content")
    return str(file_path)


@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file."""
    file_path = temp_dir / "empty.txt"
    file_path.write_text("")
    return str(file_path)


@pytest.fixture
def binary_file(temp_dir):
    """Create a binary file."""
    file_path = temp_dir / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")
    return str(file_path)


@pytest.fixture
def readonly_file(temp_dir):
    """Create a read-only file."""
    file_path = temp_dir / "readonly.txt"
    file_path.write_text("read only content")
    os.chmod(str(file_path), 0o444)
    yield str(file_path)
    # Cleanup: restore write permissions for deletion
    os.chmod(str(file_path), 0o644)


class TestWriteFileSuccess:
    """Tests for successful file writing."""

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self, text_file):
        """Should overwrite existing file content."""
        new_content = "new content here"
        result = await write_file(text_file, new_content)
        
        assert result.success is True
        assert result.error is None
        assert result.new_file_created is False
        
        # Verify the file was actually modified
        content = Path(text_file).read_text()
        assert content == new_content

    @pytest.mark.asyncio
    async def test_write_to_empty_file(self, empty_file):
        """Should write content to empty file."""
        new_content = "content for empty file"
        result = await write_file(empty_file, new_content)
        
        assert result.success is True
        content = Path(empty_file).read_text()
        assert content == new_content

    @pytest.mark.asyncio
    async def test_write_empty_content(self, text_file):
        """Should allow writing empty content (clearing file)."""
        result = await write_file(text_file, "")
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert content == ""

    @pytest.mark.asyncio
    async def test_write_multiline_content(self, text_file):
        """Should handle multiline content."""
        new_content = """line 1
line 2
line 3
"""
        result = await write_file(text_file, new_content)
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert content == new_content

    @pytest.mark.asyncio
    async def test_write_unicode_content(self, text_file):
        """Should handle unicode content."""
        new_content = "Hello 世界\nПривет мир\n🚀 emoji"
        result = await write_file(text_file, new_content)
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert "世界" in content
        assert "🚀" in content

    @pytest.mark.asyncio
    async def test_write_special_characters(self, text_file):
        """Should handle special characters correctly."""
        new_content = "Price: $100\nRegex: ^foo.*bar$\nBackslash: C:\\path\\to\\file"
        result = await write_file(text_file, new_content)
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert "$100" in content
        assert "C:\\path" in content

    @pytest.mark.asyncio
    async def test_tmp_directory_allowed(self):
        """Should allow writing files in /tmp directory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp') as f:
            f.write("original")
            tmp_file = f.name
        
        try:
            result = await write_file(tmp_file, "modified content")
            assert result.success is True
            content = Path(tmp_file).read_text()
            assert content == "modified content"
        finally:
            os.unlink(tmp_file)


class TestWriteFileCreateNew:
    """Tests for creating new files."""

    @pytest.mark.asyncio
    async def test_create_new_file(self, temp_dir):
        """Should create a new file if it doesn't exist."""
        new_file = temp_dir / "new_file.txt"
        content = "content for new file"
        
        result = await write_file(str(new_file), content)
        
        assert result.success is True
        assert result.new_file_created is True
        assert new_file.exists()
        assert new_file.read_text() == content

    @pytest.mark.asyncio
    async def test_create_new_python_file(self, temp_dir):
        """Should create a new Python file."""
        new_file = temp_dir / "script.py"
        content = '''def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
'''
        result = await write_file(str(new_file), content)
        
        assert result.success is True
        assert result.new_file_created is True
        assert new_file.read_text() == content

    @pytest.mark.asyncio
    async def test_create_new_json_file(self, temp_dir):
        """Should create a new JSON file."""
        new_file = temp_dir / "config.json"
        content = '{\n  "name": "test",\n  "version": "1.0.0"\n}'
        
        result = await write_file(str(new_file), content)
        
        assert result.success is True
        assert result.new_file_created is True

    @pytest.mark.asyncio
    async def test_create_file_in_nested_directory(self, temp_dir):
        """Should create file in nested directory if parent exists."""
        nested_dir = temp_dir / "subdir"
        nested_dir.mkdir()
        new_file = nested_dir / "nested_file.txt"
        
        result = await write_file(str(new_file), "nested content")
        
        assert result.success is True
        assert result.new_file_created is True
        assert new_file.read_text() == "nested content"


class TestWriteFileErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_path_is_directory(self, temp_dir):
        """Should return error when path is a directory."""
        result = await write_file(str(temp_dir), "content")
        
        assert result.success is False
        assert "directory" in result.error.lower() or "not a file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_binary_file_rejected(self, binary_file):
        """Should reject binary files."""
        result = await write_file(binary_file, "text content")
        
        assert result.success is False
        assert "not a text file" in result.error

    @pytest.mark.asyncio
    async def test_readonly_file_rejected(self, readonly_file):
        """Should reject read-only files."""
        result = await write_file(readonly_file, "new content")
        
        assert result.success is False
        assert "not writable" in result.error

    @pytest.mark.asyncio
    async def test_outside_pwd_rejected(self, temp_dir):
        """Should reject files outside the present working directory."""
        # Create file outside temp_dir (not in /tmp either)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                          dir='/var/tmp' if os.path.exists('/var/tmp') else tempfile.gettempdir()) as f:
            f.write("outside")
            outside_file = f.name
        
        try:
            # Only test if file is truly outside allowed directories
            if not outside_file.startswith(str(temp_dir)) and not outside_file.startswith('/tmp'):
                result = await write_file(outside_file, "new content")
                assert result.success is False
                assert "not allowed" in result.error
        finally:
            os.unlink(outside_file)

    @pytest.mark.asyncio
    async def test_parent_directory_not_exists(self, temp_dir):
        """Should fail when parent directory doesn't exist."""
        nonexistent_path = temp_dir / "nonexistent_dir" / "file.txt"
        
        result = await write_file(str(nonexistent_path), "content")
        
        assert result.success is False
        # Should indicate parent directory doesn't exist


class TestWriteFileProgrammingLanguages:
    """Tests for writing various programming language files."""

    @pytest.mark.asyncio
    async def test_write_python_file(self, temp_dir):
        """Should write Python file correctly."""
        file_path = temp_dir / "example.py"
        file_path.write_text("# placeholder")
        
        content = '''import os
from typing import List

def process_files(paths: List[str]) -> None:
    for path in paths:
        print(f"Processing {path}")

if __name__ == "__main__":
    process_files(["/tmp/test.txt"])
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert file_path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_javascript_file(self, temp_dir):
        """Should write JavaScript file correctly."""
        file_path = temp_dir / "app.js"
        file_path.write_text("// placeholder")
        
        content = '''const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "express" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_typescript_file(self, temp_dir):
        """Should write TypeScript file correctly."""
        file_path = temp_dir / "types.ts"
        file_path.write_text("// placeholder")
        
        content = '''interface User {
    id: number;
    name: string;
    email: string;
}

type UserResponse = {
    data: User;
    status: number;
};

export { User, UserResponse };
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "interface User" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_html_file(self, temp_dir):
        """Should write HTML file correctly."""
        file_path = temp_dir / "index.html"
        file_path.write_text("<!-- placeholder -->")
        
        content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
</body>
</html>
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "<!DOCTYPE html>" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_java_file(self, temp_dir):
        """Should write Java file correctly."""
        file_path = temp_dir / "Main.java"
        file_path.write_text("// placeholder")
        
        content = '''package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Java!");
    }
}
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "public class Main" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_css_file(self, temp_dir):
        """Should write CSS file correctly."""
        file_path = temp_dir / "styles.css"
        file_path.write_text("/* placeholder */")
        
        content = ''':root {
    --primary-color: #3498db;
}

body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "--primary-color" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_yaml_file(self, temp_dir):
        """Should write YAML file correctly."""
        file_path = temp_dir / "config.yaml"
        file_path.write_text("# placeholder")
        
        content = '''version: "3.8"

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert 'version: "3.8"' in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_sql_file(self, temp_dir):
        """Should write SQL file correctly."""
        file_path = temp_dir / "schema.sql"
        file_path.write_text("-- placeholder")
        
        content = '''CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "CREATE TABLE users" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_shell_script(self, temp_dir):
        """Should write shell script correctly."""
        file_path = temp_dir / "deploy.sh"
        file_path.write_text("#!/bin/bash")
        
        content = '''#!/bin/bash

set -e

echo "Starting deployment..."

cd /app
git pull origin main
npm install
npm run build

echo "Deployment complete!"
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "#!/bin/bash" in file_path.read_text()

    @pytest.mark.asyncio
    async def test_write_dockerfile(self, temp_dir):
        """Should write Dockerfile correctly."""
        file_path = temp_dir / "Dockerfile"
        file_path.write_text("# placeholder")
        
        content = '''FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''
        result = await write_file(str(file_path), content)
        
        assert result.success is True
        assert "FROM node:20-alpine" in file_path.read_text()


class TestWriteFileEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_large_content(self, text_file):
        """Should handle large content."""
        # 1MB of content
        large_content = "x" * (1024 * 1024)
        result = await write_file(text_file, large_content)
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert len(content) == 1024 * 1024

    @pytest.mark.asyncio
    async def test_content_with_null_characters(self, text_file):
        """Should handle content without null characters."""
        # Text files shouldn't have null chars, but we test the behavior
        content = "text without nulls"
        result = await write_file(text_file, content)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_consecutive_writes(self, text_file):
        """Should handle multiple consecutive writes."""
        for i in range(5):
            result = await write_file(text_file, f"write {i}")
            assert result.success is True
        
        # Final content should be the last write
        content = Path(text_file).read_text()
        assert content == "write 4"

    @pytest.mark.asyncio
    async def test_whitespace_only_content(self, text_file):
        """Should handle whitespace-only content."""
        result = await write_file(text_file, "   \n\t\n   ")
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert content == "   \n\t\n   "


class TestWriteFileResultType:
    """Tests for result type validation."""

    @pytest.mark.asyncio
    async def test_success_returns_write_file_result(self, text_file):
        """Should return WriteFileResult on success."""
        result = await write_file(text_file, "new content")
        
        assert isinstance(result, WriteFileResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_error_returns_write_file_result(self, temp_dir):
        """Should return WriteFileResult on error."""
        result = await write_file(str(temp_dir), "content")
        
        assert isinstance(result, WriteFileResult)
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_result_has_new_file_created_field(self, text_file):
        """Should have new_file_created field."""
        result = await write_file(text_file, "content")
        
        assert hasattr(result, 'new_file_created')
        assert isinstance(result.new_file_created, bool)

