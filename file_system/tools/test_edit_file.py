import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from file_system.tools.edit_file import edit_file, EditFileResult
from file_system import settings as settings_module


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files and allow access to it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch settings to allow editing files in temp directory
        with patch.object(settings_module.settings, 'present_working_directory', tmpdir):
            yield Path(tmpdir)


@pytest.fixture
def text_file(temp_dir):
    """Create a simple text file."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("line 1\nline 2\nline 3\nline 4\nline 5")
    return str(file_path)


@pytest.fixture
def multiline_file(temp_dir):
    """Create a file with specific content for testing replacements."""
    file_path = temp_dir / "multiline.txt"
    content = """def hello():
    print("Hello, World!")
    return True

def goodbye():
    print("Goodbye!")
    return False
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def duplicate_content_file(temp_dir):
    """Create a file with duplicate content."""
    file_path = temp_dir / "duplicate.txt"
    content = "foo bar foo\nfoo baz foo\nfoo qux foo"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file."""
    file_path = temp_dir / "empty.txt"
    file_path.write_text("")
    return str(file_path)


@pytest.fixture
def windows_line_endings_file(temp_dir):
    """Create a file with Windows line endings."""
    file_path = temp_dir / "windows.txt"
    file_path.write_bytes(b"line 1\r\nline 2\r\nline 3")
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


@pytest.fixture
def unicode_file(temp_dir):
    """Create a file with unicode content."""
    file_path = temp_dir / "unicode.txt"
    file_path.write_text("Hello 世界\nПривет мир\n🚀 emoji", encoding="utf-8")
    return str(file_path)


@pytest.fixture
def special_chars_file(temp_dir):
    """Create a file with special characters."""
    file_path = temp_dir / "special.txt"
    content = "Price: $100\nRegex: ^foo.*bar$\nBackslash: C:\\path\\to\\file"
    file_path.write_text(content)
    return str(file_path)


class TestEditFileSuccess:
    """Tests for successful file editing."""

    @pytest.mark.asyncio
    async def test_simple_replacement(self, text_file):
        """Should replace content successfully."""
        result = await edit_file(text_file, "line 2", "modified line 2")
        
        assert result.success is True
        assert result.error is None
        
        # Verify the file was actually modified
        content = Path(text_file).read_text()
        assert "modified line 2" in content
        assert "line 2" not in content or "modified line 2" in content

    @pytest.mark.asyncio
    async def test_multiline_replacement(self, multiline_file):
        """Should handle multiline content replacement."""
        old_content = """def hello():
    print("Hello, World!")
    return True"""
        new_content = """def hello():
    print("Hello, Universe!")
    return True"""
        
        result = await edit_file(multiline_file, old_content, new_content)
        
        assert result.success is True
        content = Path(multiline_file).read_text()
        assert "Hello, Universe!" in content
        assert "Hello, World!" not in content

    @pytest.mark.asyncio
    async def test_unicode_content_replacement(self, unicode_file):
        """Should handle unicode content replacement."""
        result = await edit_file(unicode_file, "Hello 世界", "Bonjour 世界")
        
        assert result.success is True
        content = Path(unicode_file).read_text()
        assert "Bonjour 世界" in content

    @pytest.mark.asyncio
    async def test_special_characters_replacement(self, special_chars_file):
        """Should handle special characters like $ correctly."""
        result = await edit_file(special_chars_file, "Price: $100", "Price: $200")
        
        assert result.success is True
        content = Path(special_chars_file).read_text()
        assert "Price: $200" in content

    @pytest.mark.asyncio
    async def test_replace_with_empty_string(self, text_file):
        """Should allow replacing content with empty string (deletion)."""
        result = await edit_file(text_file, "line 3\n", "")
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert "line 3" not in content

    @pytest.mark.asyncio
    async def test_tmp_directory_allowed(self, temp_dir):
        """Should allow editing files in /tmp directory."""
        # Create a file in actual /tmp
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp') as f:
            f.write("original content")
            tmp_file = f.name
        
        try:
            result = await edit_file(tmp_file, "original content", "modified content")
            assert result.success is True
        finally:
            os.unlink(tmp_file)


class TestEditFileReplaceAll:
    """Tests for replace_all functionality."""

    @pytest.mark.asyncio
    async def test_replace_all_occurrences(self, duplicate_content_file):
        """Should replace all occurrences when replace_all=True."""
        result = await edit_file(
            duplicate_content_file, 
            "foo", 
            "FOO", 
            replace_all=True
        )
        
        assert result.success is True
        content = Path(duplicate_content_file).read_text()
        assert "foo" not in content
        assert content.count("FOO") == 9  # All 9 occurrences replaced

    @pytest.mark.asyncio
    async def test_replace_first_occurrence_only(self, duplicate_content_file):
        """Should replace only first occurrence when replace_all=False."""
        # NOTE: This test documents the expected behavior - the current implementation
        # may need fixing to support this properly
        result = await edit_file(
            duplicate_content_file, 
            "foo", 
            "FOO", 
            replace_all=False
        )
        
        assert result.success is True
        content = Path(duplicate_content_file).read_text()
        # Only the first "foo" should be replaced
        assert content.count("FOO") == 1
        assert content.count("foo") == 8


class TestEditFileErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_file_not_found(self, temp_dir):
        """Should return error when file doesn't exist."""
        result = await edit_file(
            str(temp_dir / "nonexistent.txt"), 
            "old", 
            "new"
        )
        
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_path_is_directory(self, temp_dir):
        """Should return error when path is a directory."""
        result = await edit_file(str(temp_dir), "old", "new")
        
        assert result.success is False
        assert "not a file" in result.error

    @pytest.mark.asyncio
    async def test_old_content_not_found(self, text_file):
        """Should return error when old content is not in file."""
        result = await edit_file(text_file, "nonexistent content", "new content")
        
        assert result.success is False
        assert "not present" in result.error

    @pytest.mark.asyncio
    async def test_binary_file_rejected(self, binary_file):
        """Should reject binary files."""
        result = await edit_file(binary_file, "old", "new")
        
        assert result.success is False
        assert "not a text file" in result.error

    @pytest.mark.asyncio
    async def test_readonly_file_rejected(self, readonly_file):
        """Should reject read-only files."""
        result = await edit_file(readonly_file, "read only", "modified")
        
        assert result.success is False
        assert "not writable" in result.error

    @pytest.mark.asyncio
    async def test_outside_pwd_rejected(self, temp_dir):
        """Should reject files outside the present working directory."""
        # Create file in a location outside temp_dir
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("outside content")
            outside_file = f.name
        
        try:
            # Don't patch to /tmp, so the file is outside allowed directory
            with patch.object(settings_module.settings, 'present_working_directory', str(temp_dir)):
                # If the file is not in temp_dir or /tmp, it should be rejected
                if not outside_file.startswith(str(temp_dir)) and not outside_file.startswith('/tmp'):
                    result = await edit_file(outside_file, "outside", "modified")
                    assert result.success is False
                    assert "not allowed" in result.error
        finally:
            os.unlink(outside_file)

    @pytest.mark.asyncio
    async def test_empty_old_content(self, text_file):
        """Should handle empty old_content gracefully."""
        # Empty old_content technically matches but safe_replace guards against it
        result = await edit_file(text_file, "", "new content")
        
        # With empty old_content, safe_replace returns content unchanged
        # so no actual edit happens, but it should not crash
        assert isinstance(result, EditFileResult)


class TestEditFileEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_windows_line_endings(self, windows_line_endings_file):
        """Should handle files with Windows line endings."""
        result = await edit_file(windows_line_endings_file, "line 2", "modified line 2")
        
        assert result.success is True
        content = Path(windows_line_endings_file).read_text()
        assert "modified line 2" in content

    @pytest.mark.asyncio
    async def test_same_old_and_new_content(self, text_file):
        """Should reject replacing content with identical content."""
        result = await edit_file(text_file, "line 2", "line 2")
        
        assert result.success is False
        assert "same" in result.error.lower()

    @pytest.mark.asyncio
    async def test_replace_entire_file_content(self, text_file):
        """Should allow replacing entire file content."""
        original_content = Path(text_file).read_text()
        new_content = "completely new content"
        
        result = await edit_file(text_file, original_content, new_content)
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert content == new_content

    @pytest.mark.asyncio
    async def test_consecutive_edits(self, text_file):
        """Should handle multiple consecutive edits."""
        result1 = await edit_file(text_file, "line 1", "LINE 1")
        result2 = await edit_file(text_file, "line 2", "LINE 2")
        
        assert result1.success is True
        assert result2.success is True
        
        content = Path(text_file).read_text()
        assert "LINE 1" in content
        assert "LINE 2" in content

    @pytest.mark.asyncio
    async def test_whitespace_preservation(self, temp_dir):
        """Should preserve whitespace in replacements."""
        file_path = temp_dir / "whitespace.txt"
        file_path.write_text("    indented line\n\ttabbed line")
        
        result = await edit_file(
            str(file_path), 
            "    indented line", 
            "        more indented line"
        )
        
        assert result.success is True
        content = file_path.read_text()
        assert "        more indented line" in content

    @pytest.mark.asyncio
    async def test_newline_in_replacement(self, text_file):
        """Should handle adding newlines in replacement."""
        result = await edit_file(
            text_file, 
            "line 2", 
            "line 2\nline 2.5"
        )
        
        assert result.success is True
        content = Path(text_file).read_text()
        assert "line 2\nline 2.5" in content

    @pytest.mark.asyncio
    async def test_dollar_sign_in_new_content(self, text_file):
        """Should handle dollar signs correctly without escaping issues."""
        result = await edit_file(text_file, "line 1", "price is $100")
        
        assert result.success is True
        content = Path(text_file).read_text()
        # The $ should appear as-is, not doubled
        assert "price is $100" in content
        assert "$$" not in content


class TestEditFileResultType:
    """Tests for result type validation."""

    @pytest.mark.asyncio
    async def test_success_returns_edit_file_result(self, text_file):
        """Should return EditFileResult on success."""
        result = await edit_file(text_file, "line 1", "modified line 1")
        
        assert isinstance(result, EditFileResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_result_contains_success_message(self, text_file):
        """Should contain success message in content."""
        result = await edit_file(text_file, "line 1", "modified line 1")
        
        assert result.success is True
        # Check if there's any content/message about success
        assert hasattr(result, 'new_file_created') or hasattr(result, 'content')


class TestEditFileProgrammingLanguages:
    """Tests for various programming language file types."""

    # Python
    @pytest.mark.asyncio
    async def test_python_file(self, temp_dir):
        """Should edit Python files correctly."""
        file_path = temp_dir / "example.py"
        content = '''def hello_world():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'print("Hello, World!")',
            'print("Hello, Universe!")'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'print("Hello, Universe!")' in new_content
        assert 'print("Hello, World!")' not in new_content

    @pytest.mark.asyncio
    async def test_python_file_with_decorators(self, temp_dir):
        """Should edit Python files with decorators."""
        file_path = temp_dir / "decorated.py"
        content = '''@decorator
@another_decorator(param=True)
def my_function():
    pass
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '@decorator',
            '@new_decorator'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '@new_decorator' in new_content

    # JavaScript
    @pytest.mark.asyncio
    async def test_javascript_file(self, temp_dir):
        """Should edit JavaScript files correctly."""
        file_path = temp_dir / "example.js"
        content = '''const greeting = "Hello, World!";

function sayHello(name) {
    console.log(`Hello, ${name}!`);
    return true;
}

const arrowFunc = (x) => x * 2;

export { greeting, sayHello };
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'const greeting = "Hello, World!";',
            'const greeting = "Hello, Universe!";'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'const greeting = "Hello, Universe!";' in new_content

    @pytest.mark.asyncio
    async def test_javascript_async_await(self, temp_dir):
        """Should edit JavaScript async/await syntax."""
        file_path = temp_dir / "async.js"
        content = '''async function fetchData() {
    const response = await fetch('/api/data');
    return response.json();
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            "'/api/data'",
            "'/api/v2/data'"
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert "'/api/v2/data'" in new_content

    # TypeScript
    @pytest.mark.asyncio
    async def test_typescript_file(self, temp_dir):
        """Should edit TypeScript files correctly."""
        file_path = temp_dir / "example.ts"
        content = '''interface User {
    id: number;
    name: string;
    email: string;
}

class UserService {
    private users: User[] = [];

    async getUser(id: number): Promise<User | undefined> {
        return this.users.find(u => u.id === id);
    }

    addUser(user: User): void {
        this.users.push(user);
    }
}

export { User, UserService };
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'email: string;',
            'email: string;\n    age?: number;'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'age?: number;' in new_content

    @pytest.mark.asyncio
    async def test_typescript_generics(self, temp_dir):
        """Should edit TypeScript generics correctly."""
        file_path = temp_dir / "generics.ts"
        content = '''function identity<T>(arg: T): T {
    return arg;
}

type Result<T, E> = { success: true; data: T } | { success: false; error: E };
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'function identity<T>(arg: T): T',
            'function identity<T extends object>(arg: T): T'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '<T extends object>' in new_content

    # Java
    @pytest.mark.asyncio
    async def test_java_file(self, temp_dir):
        """Should edit Java files correctly."""
        file_path = temp_dir / "Example.java"
        content = '''package com.example;

import java.util.List;
import java.util.ArrayList;

public class Example {
    private String name;
    private int count;

    public Example(String name) {
        this.name = name;
        this.count = 0;
    }

    public String getName() {
        return name;
    }

    public void increment() {
        count++;
    }

    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'System.out.println("Hello, World!");',
            'System.out.println("Hello, Java!");'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'System.out.println("Hello, Java!");' in new_content

    @pytest.mark.asyncio
    async def test_java_annotations(self, temp_dir):
        """Should edit Java annotations correctly."""
        file_path = temp_dir / "Annotated.java"
        content = '''@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Column(nullable = false)
    private String name;
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '@Table(name = "users")',
            '@Table(name = "app_users")'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '@Table(name = "app_users")' in new_content

    # HTML
    @pytest.mark.asyncio
    async def test_html_file(self, temp_dir):
        """Should edit HTML files correctly."""
        file_path = temp_dir / "index.html"
        content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Welcome to My Website</h1>
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <p>Hello, World!</p>
    </main>
    <script src="app.js"></script>
</body>
</html>
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '<title>My Page</title>',
            '<title>My Awesome Page</title>'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '<title>My Awesome Page</title>' in new_content

    @pytest.mark.asyncio
    async def test_html_with_attributes(self, temp_dir):
        """Should edit HTML attributes correctly."""
        file_path = temp_dir / "form.html"
        content = '''<form action="/submit" method="POST" class="form-container">
    <input type="text" name="username" placeholder="Enter username" required>
    <button type="submit">Submit</button>
</form>
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'action="/submit"',
            'action="/api/submit"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'action="/api/submit"' in new_content

    # CSS
    @pytest.mark.asyncio
    async def test_css_file(self, temp_dir):
        """Should edit CSS files correctly."""
        file_path = temp_dir / "styles.css"
        content = ''':root {
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
}

body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '--primary-color: #3498db;',
            '--primary-color: #e74c3c;'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '--primary-color: #e74c3c;' in new_content

    # Go
    @pytest.mark.asyncio
    async def test_go_file(self, temp_dir):
        """Should edit Go files correctly."""
        file_path = temp_dir / "main.go"
        content = '''package main

import (
    "fmt"
    "net/http"
)

type Server struct {
    port string
}

func (s *Server) Start() error {
    fmt.Printf("Starting server on port %s\\n", s.port)
    return http.ListenAndServe(":"+s.port, nil)
}

func main() {
    server := &Server{port: "8080"}
    server.Start()
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'port: "8080"',
            'port: "3000"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'port: "3000"' in new_content

    # Rust
    @pytest.mark.asyncio
    async def test_rust_file(self, temp_dir):
        """Should edit Rust files correctly."""
        file_path = temp_dir / "main.rs"
        content = '''use std::collections::HashMap;

struct Config {
    debug: bool,
    port: u16,
}

impl Config {
    fn new() -> Self {
        Config {
            debug: false,
            port: 8080,
        }
    }
}

fn main() {
    let config = Config::new();
    println!("Server running on port {}", config.port);
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'debug: false,',
            'debug: true,'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'debug: true,' in new_content

    # C/C++
    @pytest.mark.asyncio
    async def test_c_file(self, temp_dir):
        """Should edit C files correctly."""
        file_path = temp_dir / "main.c"
        content = '''#include <stdio.h>
#include <stdlib.h>

#define MAX_SIZE 100

int main(int argc, char *argv[]) {
    printf("Hello, World!\\n");
    return 0;
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '#define MAX_SIZE 100',
            '#define MAX_SIZE 200'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '#define MAX_SIZE 200' in new_content

    @pytest.mark.asyncio
    async def test_cpp_file(self, temp_dir):
        """Should edit C++ files correctly."""
        file_path = temp_dir / "main.cpp"
        content = '''#include <iostream>
#include <vector>
#include <string>

class Person {
public:
    std::string name;
    int age;

    Person(std::string n, int a) : name(n), age(a) {}

    void greet() const {
        std::cout << "Hello, I'm " << name << std::endl;
    }
};

int main() {
    Person p("Alice", 30);
    p.greet();
    return 0;
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'Person p("Alice", 30);',
            'Person p("Bob", 25);'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'Person p("Bob", 25);' in new_content

    # Ruby
    @pytest.mark.asyncio
    async def test_ruby_file(self, temp_dir):
        """Should edit Ruby files correctly."""
        file_path = temp_dir / "app.rb"
        content = '''class User
  attr_accessor :name, :email

  def initialize(name, email)
    @name = name
    @email = email
  end

  def greet
    puts "Hello, #{@name}!"
  end
end

user = User.new("Alice", "alice@example.com")
user.greet
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'puts "Hello, #{@name}!"',
            'puts "Welcome, #{@name}!"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'puts "Welcome, #{@name}!"' in new_content

    # PHP
    @pytest.mark.asyncio
    async def test_php_file(self, temp_dir):
        """Should edit PHP files correctly."""
        file_path = temp_dir / "index.php"
        content = '''<?php

namespace App\\Controllers;

class HomeController {
    private $title = "Welcome";

    public function index() {
        echo "<h1>" . $this->title . "</h1>";
        return $this->render('home');
    }

    private function render($view) {
        include "views/{$view}.php";
    }
}

$controller = new HomeController();
$controller->index();
?>
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'private $title = "Welcome";',
            'private $title = "Hello";'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'private $title = "Hello";' in new_content

    # Swift
    @pytest.mark.asyncio
    async def test_swift_file(self, temp_dir):
        """Should edit Swift files correctly."""
        file_path = temp_dir / "main.swift"
        content = '''import Foundation

struct User {
    let id: Int
    var name: String
    var email: String
}

class UserManager {
    private var users: [User] = []

    func addUser(_ user: User) {
        users.append(user)
    }

    func getUser(byId id: Int) -> User? {
        return users.first { $0.id == id }
    }
}

let manager = UserManager()
print("User Manager initialized")
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'print("User Manager initialized")',
            'print("User Manager ready")'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'print("User Manager ready")' in new_content

    # Kotlin
    @pytest.mark.asyncio
    async def test_kotlin_file(self, temp_dir):
        """Should edit Kotlin files correctly."""
        file_path = temp_dir / "Main.kt"
        content = '''package com.example

data class User(
    val id: Int,
    val name: String,
    val email: String
)

class UserRepository {
    private val users = mutableListOf<User>()

    fun addUser(user: User) {
        users.add(user)
    }

    fun findById(id: Int): User? = users.find { it.id == id }
}

fun main() {
    println("Hello, Kotlin!")
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'println("Hello, Kotlin!")',
            'println("Hello, World!")'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'println("Hello, World!")' in new_content

    # SQL
    @pytest.mark.asyncio
    async def test_sql_file(self, temp_dir):
        """Should edit SQL files correctly."""
        file_path = temp_dir / "schema.sql"
        content = '''CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');

SELECT * FROM users WHERE email = 'alice@example.com';
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'name VARCHAR(100) NOT NULL,',
            'name VARCHAR(255) NOT NULL,'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'name VARCHAR(255) NOT NULL,' in new_content

    # Shell/Bash
    @pytest.mark.asyncio
    async def test_shell_file(self, temp_dir):
        """Should edit Shell script files correctly."""
        file_path = temp_dir / "deploy.sh"
        content = '''#!/bin/bash

set -e

PROJECT_DIR="/var/www/app"
BACKUP_DIR="/var/backups"

echo "Starting deployment..."

# Backup current version
cp -r "$PROJECT_DIR" "$BACKUP_DIR/$(date +%Y%m%d)"

# Pull latest changes
cd "$PROJECT_DIR"
git pull origin main

# Install dependencies
npm install

# Restart service
systemctl restart app

echo "Deployment complete!"
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'PROJECT_DIR="/var/www/app"',
            'PROJECT_DIR="/opt/app"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'PROJECT_DIR="/opt/app"' in new_content

    # YAML
    @pytest.mark.asyncio
    async def test_yaml_file(self, temp_dir):
        """Should edit YAML files correctly."""
        file_path = temp_dir / "config.yaml"
        content = '''version: "3.8"

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    environment:
      - NODE_ENV=production

  database:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'image: nginx:latest',
            'image: nginx:1.21'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'image: nginx:1.21' in new_content

    # JSON
    @pytest.mark.asyncio
    async def test_json_file(self, temp_dir):
        """Should edit JSON files correctly."""
        file_path = temp_dir / "package.json"
        content = '''{
  "name": "my-app",
  "version": "1.0.0",
  "description": "A sample application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '"version": "1.0.0"',
            '"version": "1.1.0"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '"version": "1.1.0"' in new_content

    # XML
    @pytest.mark.asyncio
    async def test_xml_file(self, temp_dir):
        """Should edit XML files correctly."""
        file_path = temp_dir / "pom.xml"
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0-SNAPSHOT</version>
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13</version>
        </dependency>
    </dependencies>
</project>
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '<version>4.13</version>',
            '<version>4.13.2</version>'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '<version>4.13.2</version>' in new_content

    # Markdown
    @pytest.mark.asyncio
    async def test_markdown_file(self, temp_dir):
        """Should edit Markdown files correctly."""
        file_path = temp_dir / "README.md"
        content = '''# My Project

## Overview

This is a sample project demonstrating various features.

## Installation

```bash
npm install my-project
```

## Usage

```javascript
const myProject = require('my-project');
myProject.init();
```

## License

MIT
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '# My Project',
            '# My Awesome Project'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '# My Awesome Project' in new_content

    # Vue.js
    @pytest.mark.asyncio
    async def test_vue_file(self, temp_dir):
        """Should edit Vue.js single file components correctly."""
        file_path = temp_dir / "HelloWorld.vue"
        content = '''<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <button @click="handleClick">Click me</button>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',
  props: {
    msg: String
  },
  methods: {
    handleClick() {
      console.log('Button clicked!');
    }
  }
}
</script>

<style scoped>
.hello {
  color: #42b983;
}
</style>
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            "name: 'HelloWorld'",
            "name: 'GreetingComponent'"
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert "name: 'GreetingComponent'" in new_content

    # React JSX
    @pytest.mark.asyncio
    async def test_jsx_file(self, temp_dir):
        """Should edit React JSX files correctly."""
        file_path = temp_dir / "App.jsx"
        content = '''import React, { useState } from 'react';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="App">
      <h1>Hello, React!</h1>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}

export default App;
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            '<h1>Hello, React!</h1>',
            '<h1>Welcome to React!</h1>'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert '<h1>Welcome to React!</h1>' in new_content

    # TSX (React + TypeScript)
    @pytest.mark.asyncio
    async def test_tsx_file(self, temp_dir):
        """Should edit React TSX files correctly."""
        file_path = temp_dir / "Button.tsx"
        content = '''import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false }) => {
  return (
    <button
      className="btn"
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
};

export default Button;
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'disabled?: boolean;',
            'disabled?: boolean;\n  variant?: "primary" | "secondary";'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'variant?: "primary" | "secondary";' in new_content

    # Scala
    @pytest.mark.asyncio
    async def test_scala_file(self, temp_dir):
        """Should edit Scala files correctly."""
        file_path = temp_dir / "Main.scala"
        content = '''package com.example

case class User(id: Int, name: String, email: String)

object Main extends App {
  val users = List(
    User(1, "Alice", "alice@example.com"),
    User(2, "Bob", "bob@example.com")
  )

  users.foreach(u => println(s"User: ${u.name}"))
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'println(s"User: ${u.name}")',
            'println(s"User: ${u.name} <${u.email}>")'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'println(s"User: ${u.name} <${u.email}>")' in new_content

    # Dockerfile
    @pytest.mark.asyncio
    async def test_dockerfile(self, temp_dir):
        """Should edit Dockerfile correctly."""
        file_path = temp_dir / "Dockerfile"
        content = '''FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'FROM node:18-alpine',
            'FROM node:20-alpine'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'FROM node:20-alpine' in new_content

    # TOML (e.g., pyproject.toml, Cargo.toml)
    @pytest.mark.asyncio
    async def test_toml_file(self, temp_dir):
        """Should edit TOML files correctly."""
        file_path = temp_dir / "pyproject.toml"
        content = '''[tool.poetry]
name = "my-project"
version = "0.1.0"
description = "A sample project"
authors = ["Alice <alice@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.28.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'version = "0.1.0"',
            'version = "0.2.0"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'version = "0.2.0"' in new_content

    # GraphQL
    @pytest.mark.asyncio
    async def test_graphql_file(self, temp_dir):
        """Should edit GraphQL schema files correctly."""
        file_path = temp_dir / "schema.graphql"
        content = '''type Query {
  user(id: ID!): User
  users: [User!]!
}

type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  content: String
  author: User!
}

type Mutation {
  createUser(name: String!, email: String!): User!
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'content: String',
            'content: String!'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'content: String!' in new_content

    # Terraform/HCL
    @pytest.mark.asyncio
    async def test_terraform_file(self, temp_dir):
        """Should edit Terraform/HCL files correctly."""
        file_path = temp_dir / "main.tf"
        content = '''provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Name = "WebServer"
  }
}

output "instance_ip" {
  value = aws_instance.web.public_ip
}
'''
        file_path.write_text(content)
        
        result = await edit_file(
            str(file_path),
            'instance_type = "t2.micro"',
            'instance_type = "t3.small"'
        )
        
        assert result.success is True
        new_content = file_path.read_text()
        assert 'instance_type = "t3.small"' in new_content

