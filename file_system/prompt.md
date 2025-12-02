# File System Tools Guidelines

You have access to file system tools to read, write, and edit files on the local filesystem.

## Available Tools

### read_file
Read content from a file with optional line offset and limit.

```
read_file(file_path, limit?, offset?)
```

- `file_path`: Absolute path to the file (required)
- `limit`: Maximum number of lines to read (default: 2000)
- `offset`: Number of lines to skip from the beginning (default: 0)

**Returns**: File content with line numbers in `cat -n` format

### write_file
Write content to a file. Creates the file if it doesn't exist.

```
write_file(file_path, content)
```

- `file_path`: Absolute path to the file (required)
- `content`: The content to write (required)

**Returns**: Success message with `new_file_created` flag

### edit_file
Edit a file by replacing specific content.

```
edit_file(file_path, old_content, new_content, replace_all?)
```

- `file_path`: Absolute path to the file (required)
- `old_content`: The content to find and replace (required)
- `new_content`: The content to replace with (required)
- `replace_all`: Replace all occurrences if true, only first if false (default: false)

**Returns**: Success message after editing

## When to Use Each Tool

| Tool | Use Case |
|------|----------|
| `read_file` | Inspect file contents, understand code structure, verify changes |
| `write_file` | Create new files, completely overwrite existing files |
| `edit_file` | Make targeted changes to existing files, refactoring |

## Key Rules

### Do's
- Always use **absolute paths** for file operations
- **Read before editing** - understand the file structure first
- Use `edit_file` for targeted changes to preserve surrounding content
- Use `write_file` only when creating new files or complete rewrites
- Include enough context in `old_content` to ensure unique matches

### Don'ts
- Don't use relative paths
- Don't edit files outside the present working directory (security restriction)
- Don't use `edit_file` with `old_content` that matches multiple locations (unless using `replace_all`)
- Don't edit binary files (only text files are supported)


## Examples

### Reading a file
```
read_file("/path/to/project/src/main.py")
```

### Reading with pagination (for large files)
```
read_file("/path/to/project/logs/app.log", limit=100, offset=500)
```

### Creating a new file
```
write_file("/path/to/project/src/utils.py", "def helper():\n    pass\n")
```

### Editing specific content
```
edit_file(
    "/path/to/project/config.json",
    '"version": "1.0.0"',
    '"version": "1.1.0"'
)
```

### Renaming a variable everywhere
```
edit_file(
    "/path/to/project/src/app.py",
    "old_variable_name",
    "new_variable_name",
    replace_all=True
)
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "File does not exist" | Invalid path | Verify the file path is correct |
| "Path is not a file" | Path points to directory | Use a file path, not directory |
| "File is not writable" | Permission denied | Check file permissions |
| "File is not a text file" | Binary file detected | Only text files are supported |
| "Old content is not present" | Content not found | Verify `old_content` matches exactly |
| "Parent directory does not exist" | Missing parent folder | Create parent directories first |

## Best Practices

1. **Read first, edit second**: Always inspect a file before making changes
2. **Use specific context**: Include surrounding lines in `old_content` for unique matching
3. **Verify after editing**: Read the file again to confirm changes were applied correctly
4. **Batch related reads**: Read multiple files in parallel when exploring a codebase
5. **Preserve formatting**: Match the existing indentation and style when editing

