# Command Line Tool Guidelines

You have access to a command execution tool that allows you to run bash commands.

## Available Tool

### bash
Execute a bash command and get the output.

```
bash(command, description, timeout, run_in_background)
```

- `command`: The shell command to execute (required)
- `description`: Clear, concise description of what this command does in 5-10 words, in active voice. 
    Examples:
    Input: ls
    Output: List files in current directory

    Input: git status
    Output: Show working tree status

    Input: npm install
    Output: Install package dependencies

    Input: mkdir foo
    Output: Create directory 'foo' 
- `timeout`: Timeout in seconds (optional, default: 60, max: 300)
- `run_in_background`: Set to true to run this command in the background. Use Returned PID to read the output later.

**Returns**: CommandResult with stdout, stderr, return_code, and success status

## When to Use

Use `execute_command` for:
- **Package management**: `npm install`, `pip install`, `uv add`
- **Build commands**: `npm run build`, `python -m pytest`
- **Git operations**: `git status`, `git add`, `git commit`
- **Running scripts**: `python script.py`, `node app.js`
- **System info**: `ls`, `pwd`, `cat`, `head`, `tail`
- **Process management**: Starting/stopping services

## Key Rules

### Do's
- Use appropriate timeouts for long-running commands
- Check command output for errors
- Use the correct working directory
- Prefer simple, single-purpose commands
- 

### Don'ts
- Don't run commands that modify system files outside the project
- Don't use interactive commands (they will hang)
- Don't run infinite loops or long-running daemons without backgrounding
- Don't execute untrusted user input as commands

## Security

The tool has built-in security features:
- **Blocked commands**: Destructive commands like `rm -rf /` are blocked
- **Dangerous patterns**: Commands with `sudo`, `rm -rf`, etc. trigger warnings
- **Directory restrictions**: Only allowed in project directory and `/tmp`
- **Timeouts**: Prevents runaway processes

## Examples

### Install dependencies
```
execute_command("npm install")
execute_command("pip install -r requirements.txt")
```

### Run tests
```
execute_command("python -m pytest -v", timeout=120)
execute_command("npm test")
```

### Git operations
```
execute_command("git status")
execute_command("git add .")
execute_command("git commit -m 'Add feature'")
```

### Check output
```
execute_command("ls -la")
execute_command("cat package.json")
```

### Run in specific directory
```
execute_command("npm install", working_directory="/path/to/project")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Command is blocked" | Security restriction | Use a safer alternative |
| "Command timed out" | Took too long | Increase timeout or optimize command |
| "Directory not allowed" | Outside allowed paths | Use project directory or /tmp |
| Non-zero return code | Command failed | Check stderr for details |

## Best Practices

1. **Check before modifying**: Run `ls` or `cat` before modifying files
2. **Use timeouts**: Set appropriate timeouts for long operations
3. **Handle failures**: Check `success` and `return_code` in results
4. **Keep it simple**: Prefer simple commands over complex pipelines
5. **Be explicit**: Use full paths when needed to avoid ambiguity

