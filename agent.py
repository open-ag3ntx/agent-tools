from typing import Any
from prompt_toolkit.keys import Keys
from asyncio.exceptions import CancelledError
from packaging.utils import _
from langchain_core.runnables.schema import EventData
from msgpack import dump
import json
from todo.tools.list_todos import display_list_todos
import dis
from todo.tools.update_todo import display_update_todo
from todo.tools.create_todo import display_create_todo
from bash.tools.bash import display_bash
from bash.tools.grep import display_grep
from bash.tools.glob import display_glob
import datetime
import os
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
from rich.live import Live
from rich.markdown import Markdown
from rich.console import Console, Group
from rich.text import Text
from rich.spinner import Spinner
from rich.panel import Panel
from rich.align import Align
from base.settings import settings
from llm_client.client import client as llm_client
from file_system.tools.read_file import display_read_file, get_read_file_tool_output
from file_system.tools.write_file import display_write_file
from file_system.tools.edit_file import display_edit_file
from langchain_core.load import loads, dumps
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
import asyncio
import sys


# For terminal echo suppression
try:
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False


import select
load_dotenv()

console = Console()

BANNER = """

 █████╗  ██████╗ ██████╗ ███╗   ██╗████████╗██╗  ██╗
██╔══██╗██╔════╝ ╚════██╗████╗  ██║╚══██╔══╝╚██╗██╔╝
███████║██║  ███╗ █████╔╝██╔██╗ ██║   ██║    ╚███╔╝ 
██╔══██║██║   ██║ ╚═══██╗██║╚██╗██║   ██║    ██╔██╗ 
██║  ██║╚██████╔╝██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

"""

def print_banner():
    banner_text = Text(BANNER, style=f"bold {settings.theme_color}")
    panel = Panel(
        banner_text,
        expand=False,
        border_style=settings.theme_color,
        padding=(1, 2),
        title="[bold white]v1.0.0[/]",
        title_align="right",
        subtitle="[bold white]Coding Agent[/]",
        subtitle_align="left",
    )
    console.print(panel)
    console.print()  # Newline

def check_for_esc():
    """Check if Esc key was pressed without blocking."""
    if not HAS_TERMIOS:
        return False
    
    # Check if there's data to read on stdin
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        try:
            # Read the key
            char = sys.stdin.read(1)
            # \x1b is the escape character
            if char == '\x1b':
                return True
        except:
            pass
    return False



def create_prompt():
    with open("agent-prompt.md", "r") as f:
        agent_prompt = f.read()
    agent_prompt = agent_prompt.format(
        working_directory=settings.present_test_directory,
        is_directory_a_git_repo=settings.is_git_repo,
        platform=settings.platform,
        os_version=settings.os_version,
        todays_date=datetime.datetime.now().strftime("%Y-%m-%d"),
    )
    return agent_prompt

tools = [
    *llm_client.get_file_system_tools(),
    *llm_client.get_todo_tools(),
    *llm_client.get_bash_tools(),
    *llm_client.get_interactive_tools(),
    *llm_client.get_subagent_tool(),
    *llm_client.get_skill_tool(),
]

llm = llm_client.get_new_instance()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=create_prompt(),
)


async def get_multiline_input(prompt: str = "You: ") -> str:
    """
    Get input from user.
    - Enter: Submit
    - Shift+Enter: Newline
    """
    kb = KeyBindings()

    @kb.add(Keys.Escape, Keys.Enter)
    def _(event):
        """Submit on Alt+Enter"""
        event.current_buffer.insert_text('\n')


    @kb.add('enter')
    def _(event):
        # Enter to submit
        event.current_buffer.validate_and_handle()

    
    session = PromptSession(key_bindings=kb)
    try:
        text = await session.prompt_async(prompt, multiline=True)
        return text.strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"


async def main():
    print_banner()
    messages = []
    
    while True:
        try:
            user_input = await get_multiline_input("You: ")
            if user_input.lower() == "exit":
                console.print("Goodbye!")
                break
            if not user_input.strip():
                continue
            
            messages.append(("user", user_input))
            
            printed_count = 0
            accumulated_content = ""
            current_tool_input = ""
            
            final_messages = None
            
            fd: int | Any = sys.stdin.fileno()
            old_settings = None
            if HAS_TERMIOS:
                old_settings = termios.tcgetattr(fd)
                new_settings = termios.tcgetattr(fd)
                new_settings[3] = new_settings[3] & ~termios.ECHO
                termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)

            try:
                with Live(console=console, refresh_per_second=20, auto_refresh=True, transient=True, vertical_overflow="crop") as live:
                    live.update(Spinner("dots", text=f"[bold {settings.theme_color}]Ag3ntX: Thinking...[/] (Press Esc to Stop)"))
                    
                    if HAS_TERMIOS:
                        tty.setcbreak(fd)

                    interrupted = False
                    async for event in agent.astream_events({
                        "messages": messages
                    }, version="v2", config={"recursion_limit": 100}):
                        if check_for_esc():
                            interrupted = True
                            break

                        kind: str = event["event"]
                        data = event["data"]
                        
                        if kind == "on_chat_model_stream":
                            chunk = data.get("chunk")
                            if chunk:
                                content = chunk.content
                                if content:
                                    if isinstance(content, list):
                                        content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
                                    accumulated_content += content
                                    live.update(Markdown(f"Ag3ntX: {accumulated_content}"))
                                    
                        elif kind == "on_tool_start":
                            if accumulated_content:
                                live.console.print(Markdown(f"Ag3ntX: {accumulated_content}"))
                                accumulated_content = ""
                            
                            name = event["name"]
                            summary = f"Running tool: {name}"
                            try:
                                match name:
                                    case "read_file":
                                        input_data = data.get('input', {})
                                        if 'path' in input_data and 'file_path' not in input_data:
                                            input_data['file_path'] = input_data.pop('path')
                                        summary = display_read_file(**input_data)
                                    case "write_file":
                                        summary = display_write_file(**data.get('input', {}))
                                    case "edit_file":
                                        summary = display_edit_file(**data.get('input', {}))
                                    case 'glob':
                                        summary = display_glob(**data.get('input', {}))
                                    case 'grep':
                                        summary = display_grep(**data.get('input', {}))   
                                    case 'bash':
                                        summary = display_bash(**data.get('input', {}))
                                    case 'create_todo': 
                                        summary = display_create_todo(**data.get('input', {}))
                                    case 'update_todo':
                                        summary = display_update_todo(**data.get('input', {}))
                                    case 'list_todos':
                                        summary = display_list_todos(**data.get('input', {}))
                            except Exception as e:
                                summary = f"Running tool: {name} (formatting error: {e})"
                            
                            if isinstance(summary, str):
                                status_text = Text.from_markup(f"[bold {settings.theme_color}]Ag3ntX: {summary}:[/] ")
                                live.console.print(status_text)
                                live.update(Spinner("dots", text=f"[bold {settings.theme_color}]Ag3ntX: Waiting for tool...[/]"))
                            else:
                                live.console.print(summary) 
                                live.update(Spinner("dots", text=f"[bold {settings.theme_color}]Ag3ntX: Waiting for tool...[/]"))

                        elif kind == "on_tool_end":
                            if accumulated_content:
                                live.console.print(Markdown(f"**Ag3ntX:** {accumulated_content}"))  # ty:ignore[unresolved-reference]
                                accumulated_content = ""
                            name = event["name"]
                            tool_output = data.get("output")
                            
                            if tool_output:
                                output_summary = None
                                live.update(Spinner("dots", text=f"[bold {settings.theme_color}]Ag3ntX: Thinking...[/]"))
                        
                        elif kind == "on_chain_end":
                            if not data.get("parent_ids"):
                                output = data.get("output")
                                if isinstance(output, dict) and "messages" in output:
                                    cand_messages = output["messages"]
                                    if isinstance(cand_messages, list) and len(cand_messages) > len(messages):
                                        final_messages = cand_messages
                    
                    if interrupted:
                        live.console.print(f"[bold red]Interrupted by user (Esc pressed).[/]")
            finally:
                # Restore terminal settings
                if HAS_TERMIOS and old_settings:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            if accumulated_content:
                console.print(Markdown(f"**Ag3ntX:** {accumulated_content}"))
            console.print()  # Newline
            
            if final_messages:
                messages = final_messages
            else:
             
                if accumulated_content:
                    messages.append(AIMessage(content=accumulated_content))
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, CancelledError):
        pass