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
from rich.console import Console
from base.settings import settings as file_system_settings
from llm_client.client import client as llm_client
from file_system.tools.read_file import display_read_file, get_read_file_tool_output
from file_system.tools.write_file import display_write_file
from file_system.tools.edit_file import display_edit_file
from langchain_core.load import loads, dumps

load_dotenv()

console = Console()


def create_prompt():
    with open("agent-prompt.md", "r") as f:
        agent_prompt = f.read()
    agent_prompt = agent_prompt.format(
        working_directory=file_system_settings.present_test_directory,
        is_directory_a_git_repo=file_system_settings.is_git_repo,
        platform=file_system_settings.platform,
        os_version=file_system_settings.os_version,
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
    system_prompt=create_prompt()
)


def get_multiline_input(prompt: str = "You: ") -> str:
    """
    Get multiline input from user.
    - Single line: type and press Enter
    - Multiple lines: keep typing, press Enter twice (empty line) to submit
    """
    console.print(prompt, end="")
    lines = []
    
    while True:
        try:
            line = input()
        except EOFError:
            break
        
        # Empty line with existing content = submit
        if not line and lines:
            break
        
        # Empty line with no content = keep waiting
        if not line and not lines:
            continue
        
        lines.append(line)
    
    return "\n".join(lines)


async def main():
    console.print("AI Coding Agent Ready. Type 'exit' to quit.\n")
    
    messages = []
    
    while True:
        try:
            user_input = get_multiline_input("You: ")
            if user_input.lower() == "exit":
                console.print("Goodbye!")
                break
            if not user_input.strip():
                continue
            
            messages.append(("user", user_input))
            
            printed_count = 0
            accumulated_content = ""
            current_tool_input = ""
            
            # Track the final state to update messages at the end
            final_messages = None
            
            # transients=True is crucial to prevent "ghosting" of the live display when input starts
            with Live(console=console, refresh_per_second=1, auto_refresh=True, transient=True) as live:
                async for event in agent.astream_events({
                    "messages": messages
                }, version="v2"):
                    kind = event["event"]
                    data = event["data"]
                    
                    if kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        if chunk:
                            content = chunk.content
                            if content:
                                accumulated_content += content
                                live.update(Markdown(f"**AI:** {accumulated_content}"))
                                
                    elif kind == "on_tool_start":
                        name = event["name"]
                        summary = f"Running tool: {name}"
                        match name:
                            case "read_file":
                                input_data = data.get('input', {})
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
                        
                        # Show the tool summary temporarily
                        live.stop()
                        if isinstance(summary, str):
                            console.print(Markdown(f"**AI:** {summary}"))
                        else:
                            console.print(summary)
                        live.start()
                        
                    elif kind == "on_tool_end":
                        name = event["name"]
                        tool_output = data.get("output")
                        if tool_output:
                            summary = f"[bold orange]**Tool ({name}):**[/]"
                            match name:
                                case "read_file":
                                    summary = get_read_file_tool_output(data)
                                case _:
                                    pass
                             
                            # Print tool output permanently
                            live.stop()
                            console.print(summary)
                            live.start()
                            
                            # Restore AI message to the live display
                            live.update(Markdown(f"**AI:** {accumulated_content}"))
                    
                    elif kind == "on_chain_end":
                        # Only capture the final state from the ROOT chain (no parent_ids)
                        # This ensures we get the full state of the graph, not just a sub-chain result
                        if not data.get("parent_ids"):
                            output = data.get("output")
                            # Sanity check: ensure output has messages and it's a list
                            if isinstance(output, dict) and "messages" in output:
                                cand_messages = output["messages"]
                                if isinstance(cand_messages, list) and len(cand_messages) > len(messages):
                                    final_messages = cand_messages

            # Print the final accumulated AI content permanently
            if accumulated_content:
                console.print(Markdown(f"**AI:** {accumulated_content}"))
            console.print()  # Newline
            
            # Update history safely
            if final_messages:
                messages = final_messages
            else:
                # If we failed to capture the full state, we rely on manual append.
                # WARNING: This is lossy if tool calls happened, as we validly need the ToolMessages 
                # and the AIMessage with tool_calls set.
                # But it's better than crashing or losing the text response.
                if accumulated_content:
                    messages.append(AIMessage(content=accumulated_content))
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!")
            break


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())