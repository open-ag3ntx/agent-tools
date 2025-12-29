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
from file_system.tools.read_file import display_read_file
from file_system.tools.write_file import display_write_file
from file_system.tools.edit_file import display_edit_file

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
            user_input = get_multiline_input("\nYou: ")
            if user_input.lower() == "exit":
                console.print("Goodbye!")
                break
            if not user_input.strip():
                continue
            
            messages.append(("user", user_input))
            
            printed_count = 0
            accumulated_content = ""
            ai_started = False
            last_ai_message_index = -1  # Track which AI message we're currently streaming
            
            with Live(console=console, refresh_per_second=10, auto_refresh=True) as live:
                async for chunk in agent.astream({
                    "messages": messages
                }, stream_mode="values"):
                    all_messages = chunk["messages"]
                    
                    for idx, msg in enumerate(all_messages[printed_count:], start=printed_count):
                        if isinstance(msg, HumanMessage):
                            # User messages already displayed
                            pass
                        
                        elif isinstance(msg, ToolMessage):
                            # Tool results handled elsewhere
                            pass
                        
                        elif isinstance(msg, AIMessage):
                            # Check if this is a new AI message (reset accumulated content)
                            if idx != last_ai_message_index:
                                accumulated_content = ""
                                ai_started = False
                                last_ai_message_index = idx
                            
                            # Handle tool calls
                            if msg.tool_calls:
                                # print(msg.tool_calls)
                                for tool_call in msg.tool_calls:
                                    match tool_call["name"]:
                                        case "read_file":
                                            summary = display_read_file(**tool_call["args"])
                                        case "write_file":
                                            summary = display_write_file(**tool_call["args"])
                                        case "edit_file":
                                            summary = display_edit_file(**tool_call["args"])
                                        case 'glob':
                                            summary = display_glob(**tool_call["args"])
                                        case 'grep':
                                            summary = display_grep(**tool_call["args"])   
                                        case 'bash':
                                            summary = display_bash(**tool_call["args"])
                                        case 'create_todo': 
                                            summary = display_create_todo(**tool_call["args"])
                                        case 'update_todo':
                                            summary = display_update_todo(**tool_call["args"])
                                        case 'list_todos':
                                            summary: str = display_list_todos(**tool_call["args"])
                                        case _:
                                            summary = f'[Tool: {tool_call["name"]}]'
                                    live.stop()
                                    console.print(f"[bold orange]**AI:**[/] {summary}")
                                    live.start()
                            
                            content = msg.content
                            if content:
                                if not ai_started:
                                    ai_started = True
                                
                                new_content = ""
                                if isinstance(content, list):
                                    for block in content:
                                        if isinstance(block, dict) and block.get('type') == 'text':
                                            text = block.get('text', '')
                                            if text:
                                                new_content += text
                                        elif isinstance(block, str) and block:
                                            new_content += block
                                elif isinstance(content, str):
                                    new_content = content
                                
                                # Only update if content changed
                                if new_content != accumulated_content:
                                    accumulated_content = new_content
                                    # Update live display with markdown
                                    if accumulated_content:
                                        live.update(Markdown(f"**AI:** {accumulated_content}"))
                                        accumulated_content = None
                    
                    printed_count = len(all_messages)
            
            console.print()  # Newline after streaming
            messages = chunk["messages"]
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!")
            break


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())