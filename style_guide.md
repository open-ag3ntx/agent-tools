# Style Guide: White & Dim Purple Theme

This document defines the visual identity for the AI Coding Agent TUI and associated tools.

## Color Palette

| Name | Role | Hex / Rich Name |
| :--- | :--- | :--- |
| **Pristine White** | Main Content, AI Text | `#FFFFFF` / `bright_white` |
| **Dim Purple** | Tool Status, Spinners, Accents | `#9B59B6` / `plum3` or `medium_purple` |
| **Muted Slate** | Secondary Information, Timestamps | `#95A5A6` / `grey50` |
| **Deep Background**| Console Background | `#1A1A1A` |

## TUI Component Styling (Rich)

### 1. AI Response
- **Style**: `bright_white`
- **Prefix**: `[bold bright_white]AI:[/]`
- **Cursor**: `▎` (Standard)

### 2. Tool Execution Status
- **Style**: `medium_purple`
- **Format**: `[bold medium_purple]Running:[/] {summary}`
- **Spinner**: `Spinner("dots", text="[bold medium_purple]Thinking...[/]")`

### 3. Tool Results (Permanent)
- **Tool Header**: `[bold bright_white]**Tool ({name}):**[/]`
- **Success Tone**: Subtle purple border or underline.

## Writing Style
- **Tone**: Professional, concise, and helpful.
- **Formatting**: Use Markdown for code blocks and bolding.
- **Flow**: Preservation of chronological order (Thoughts -> Action -> Response).

## Implementation Reference (Python)
```python
from rich.style import Style
from rich.text import Text

DIM_PURPLE = "#9B59B6"
THEME_STYLE = Style(color=DIM_PURPLE, bold=True)

# Example usage:
live.update(Spinner("dots", text=Text("Thinking...", style=THEME_STYLE)))
```
