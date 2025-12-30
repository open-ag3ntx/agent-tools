import subprocess
import re
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

cmd = ["git", "diff"]  # No --color flag
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    diff_output = result.stdout
except subprocess.CalledProcessError as e:
    console.print(f"[bold red]Error running git diff: {e.stderr}[/bold red]")
    exit(1)

if not diff_output.strip():
    console.print("[yellow]No changes to display[/yellow]")
else:
    # Rich's Syntax automatically colors diff format
    syntax = Syntax(
        diff_output,
        "diff",
        theme="ansi_dark",  # or "ansi_dark", "github-dark", etc.
        line_numbers=False,
        word_wrap=False
    )
    console.print(syntax)