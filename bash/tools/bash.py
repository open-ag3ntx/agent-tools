import asyncio
import os
import shlex
from typing import Annotated, Optional

from base import bash_utils
from base.settings import settings
from base.models import CommandResult


async def bash(
    command: Annotated[str, "The shell command to execute"],
    description: Annotated[str, "A clear, concise description of what this command does in 5-10 words"],
    timeout: Annotated[int, "Timeout in seconds (default: 120, max: 600)"] = settings.default_timeout,
    run_in_background: Annotated[Optional[bool], "Whether to run the command in the background"] = False,
    working_directory: Annotated[Optional[str], "Working directory for the command"] = None,
) -> CommandResult:
    """
    Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling and security measures.

    IMPORTANT: This tool is for terminal operations like git, npm, docker, etc. DO NOT use it for file operations (reading, writing, editing, searching, finding files) - use the specialized tools for this instead.

    Before executing the command, please follow these steps:

    1. Directory Verification:
    - If the command will create new directories or files, first use `ls` to verify the parent directory exists and is the correct location
    - For example, before running `mkdir foo/bar`, first use `ls foo` to check that "foo" exists and is the intended parent directory

    2. Command Execution:
    - Always quote file paths that contain spaces with double quotes (e.g., cd "path with spaces/file.txt")
    - Examples of proper quoting:
        - cd "/Users/name/My Documents" (correct)
        - cd /Users/name/My Documents (incorrect - will fail)
        - python "/path/with spaces/script.py" (correct)
        - python /path/with spaces/script.py (incorrect - will fail)
    - After ensuring proper quoting, execute the command.
    - Capture the output of the command.

    Usage notes:
    - The command argument is required.
    - You can specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). If not specified, commands will timeout after 120000ms (2 minutes).
    - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.
    - If the output exceeds 30000 characters, output will be truncated before being returned to you.
    - You can use the `run_in_background` parameter to run the command in the background, which allows you to continue working while the command runs. You can monitor the output using the Bash tool as it becomes available. You do not need to use '&' at the end of the command when using this parameter.
    
    - Avoid using Bash with the `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`, or `echo` commands, unless explicitly instructed or when these commands are truly necessary for the task. Instead, always prefer using the dedicated tools for these commands:
        - File search: Use glob (NOT find or ls)
        - Content search: Use mgrep (NOT grep or rg)
        - Read files: Use read_file (NOT cat/head/tail)
        - Edit files: Use edit_file (NOT sed/awk)
        - Write files: Use write_file (NOT echo >/cat <<EOF)
        - Communication: Output text directly (NOT echo/printf)
    - When issuing multiple commands:
        - If the commands are independent and can run in parallel, make multiple Bash tool calls in a single message. For example, if you need to run "git status" and "git diff", send a single message with two Bash tool calls in parallel.
        - If the commands depend on each other and must run sequentially, use a single Bash call with '&&' to chain them together (e.g., `git add . && git commit -m "message" && git push`). For instance, if one operation must complete before another starts (like mkdir before cp, Write before bash for git operations, or git add before git commit), run these operations sequentially instead.
        - Use ';' only when you need to run commands sequentially but don't care if earlier commands fail
        - DO NOT use newlines to separate commands (newlines are ok in quoted strings)
    - Try to maintain your current working directory throughout the session by using absolute paths and avoiding usage of `cd`. You may use `cd` if the User explicitly requests it.
        <good-example>
        pytest /foo/bar/tests
        </good-example>
        <bad-example>
        cd /foo/bar && pytest tests
        </bad-example>

    # Committing changes with git

    Only create commits when requested by the user. If unclear, ask first. When the user asks you to create a new git commit, follow these steps carefully:

    Git Safety Protocol:
    - NEVER update the git config
    - NEVER run destructive/irreversible git commands (like push --force, hard reset, etc) unless the user explicitly requests them 
    - NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it
    - NEVER run force push to main/master, warn the user if they request it
    - Avoid git commit --amend.  ONLY use --amend when either (1) user explicitly requested amend OR (2) adding edits from pre-commit hook (additional instructions below) 
    - Before amending: ALWAYS check authorship (git log -1 --format='%an %ae')
    - NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive.

    1. You can call multiple tools in a single response. When multiple independent pieces of information are requested and all commands are likely to succeed, run multiple tool calls in parallel for optimal performance. run the following bash commands in parallel, each using the Bash tool:
    - Run a git status command to see all untracked files.
    - Run a git diff command to see both staged and unstaged changes that will be committed.
    - Run a git log command to see recent commit messages, so that you can follow this repository's commit message style.
    2. Analyze all staged changes (both previously staged and newly added) and draft a commit message:
    - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature, bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes and their purpose (i.e. "add" means a wholly new feature, "update" means an enhancement to an existing feature, "fix" means a bug fix, etc.).
    - Do not commit files that likely contain secrets (.env, credentials.json, etc). Warn the user if they specifically request to commit those files
    - Draft a concise (1-2 sentences) commit message that focuses on the "why" rather than the "what"
    - Ensure it accurately reflects the changes and their purpose
    3. You can call multiple tools in a single response. When multiple independent pieces of information are requested and all commands are likely to succeed, run multiple tool calls in parallel for optimal performance. run the following commands:
    - Add relevant untracked files to the staging area.
    - Create the commit with a message ending with:
    - Run git status after the commit completes to verify success.
    Note: git status depends on the commit completing, so run it sequentially after the commit.
    4. If the commit fails due to pre-commit hook changes, retry ONCE. If it succeeds but files were modified by the hook, verify it's safe to amend:
    - Check HEAD commit: git log -1 --format='[%h] (%an <%ae>) %s'. VERIFY it matches your commit
    - Check not pushed: git status shows "Your branch is ahead"
    - If both true: amend your commit. Otherwise: create NEW commit (never amend other developers' commits)

    Important notes:
    - NEVER run additional commands to read or explore code, besides git bash commands
    - NEVER use the TodoWrite or Task tools
    - DO NOT push to the remote repository unless the user explicitly asks you to do so
    - IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.
    - If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit
    - In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:
    <example>
    git commit -m "$(cat <<'EOF'
    Commit message here.
    EOF
    )"
    </example>
    """
    try:
        # Determine the working directory
        cwd = working_directory or settings.present_test_directory
        
        # Validate working directory
        if not os.path.exists(cwd):
            return CommandResult(
                success=False,
                error=f"Working directory does not exist: {cwd}",
                command=command,
                run_in_background=run_in_background
            )
        
        if not os.path.isdir(cwd):
            return CommandResult(
                success=False,
                error=f"Path is not a directory: {cwd}",
                command=command,
                run_in_background=run_in_background
            )
        
        if bash_utils.is_command_blocked(command):
            return CommandResult(
                success=False,
                error=f"Command is blocked for security reasons: {command}",
                command=command,
                run_in_background=run_in_background
            )
        
        # Check for dangerous patterns (warn but allow)
        dangerous_pattern = bash_utils.is_command_dangerous(command)
        if dangerous_pattern:
            return CommandResult(
                success=False,
                error=f"Command contains potentially dangerous pattern '{dangerous_pattern}'",
                command=command,
                run_in_background=run_in_background
            )

        process = await asyncio.create_subprocess_exec(
            *shlex.split(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={'PATH': '/usr/bin:/bin'}
        )
        
        try:
            if run_in_background:
                return CommandResult(
                    success=True,
                    command=command,
                    run_in_background=run_in_background,
                    process_id=process.pid
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            return CommandResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str[:30000], # return only first 30000 characters of stderr
                return_code=process.returncode,
                command=command,
                run_in_background=run_in_background,
                error=stderr_str if process.returncode != 0 else None
            )
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return CommandResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                command=command,
                timed_out=True
            )
    
    except Exception as e:
        return CommandResult(
            success=False,
            error=f"Error executing command: {str(e)}",
            command=command,
        )

