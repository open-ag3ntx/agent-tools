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
from file_system.tools.read_file import display_read_file
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
            
            with Live(console=console, refresh_per_second=12, auto_refresh=True) as live:
                async for event in agent.astream_events({
                    "messages": messages
                }, version="v1"):
                    kind = event["event"]
                    data = event["data"]
                    if kind not in ["on_chat_model_stream", "on_chain_end", "on_chat_model_end", "on_chain_stream"]:
                        print('======================================DEBUG EVENT======================================')
                        print(dumps(event, pretty=True))
                        print('=======================================================================================')
                    
                    if kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        if chunk:
                            content = chunk.content
                            if content:
                                accumulated_content += content
                                live.update(Markdown(f"**AI:** {accumulated_content}"))
                                
                    elif kind == "on_tool_start":
                        live.update(Markdown(f"**AI:** {accumulated_content}[dim]Running tool: {event['name']}...[/]"))
                        
                    elif kind == "on_tool_end":
                        tool_output = data.get("output")
                        if tool_output:
                            if hasattr(tool_output, "content"):
                                output_str = tool_output.content
                            else:
                                output_str = str(tool_output)
                                
                            live.stop()
                            console.print(f"[bold orange]**Tool ({event['name']}):**[/] {output_str}")
                            live.start()
                            # Restore AI message
                            live.update(Markdown(f"**AI:** {accumulated_content}"))
                    
                    elif kind == "on_chain_end":
                        # Attempt to capture the final state if this is the root chain ending
                        output = data.get("output")
                        if isinstance(output, dict) and "messages" in output:
                            final_messages = output["messages"]

            console.print()  # Newline
            
            # Update history
            if final_messages:
                messages = final_messages
            else:
                # Fallback if we couldn't capture state (shouldn't happen with correct LangGraph setup)
                # We manually append at least the AI response
                if accumulated_content:
                    messages.append(AIMessage(content=accumulated_content))
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!")
            break


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())