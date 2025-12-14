import datetime
import os
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.markdown import Markdown
from base.settings import settings as file_system_settings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from llm_client.client import client as llm_client

load_dotenv()


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
    *llm_client.get_subagent_tool()
]

llm = llm_client.get_new_instance()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=create_prompt()
)

console = Console()

def print_message(msg):
    """Pretty print a message with markdown formatting for text content."""
    if isinstance(msg, HumanMessage):
        print("================================ Human Message =================================")
        print(msg.content)
    elif isinstance(msg, ToolMessage):
        print("================================= Tool Message =================================")
        print(msg.content)
    elif isinstance(msg, AIMessage):
        print("================================== AI Message ==================================")
        
        # Handle tool calls
        if msg.tool_calls:
            print("Tool Calls:")
            for tool_call in msg.tool_calls:
                print(f"  {tool_call['name']} ({tool_call['id']})")
                print(f"  Args:")
                for key, value in tool_call['args'].items():
                    # Truncate long values
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"    {key}: {value_str}")
        
        # Handle text content
        content = msg.content
        if content:
            # Content can be a string or a list of content blocks
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text = block.get('text', '')
                        if text:
                            console.print(Markdown(text))
                        elif text:
                            print(text)
                    elif isinstance(block, str):
                        if text:
                            console.print(Markdown(block))
                        else:
                            print(block)
            elif isinstance(content, str) and content:
                if content:
                    console.print(Markdown(content))
                else:
                    print(content)
    else:
        # Fallback to pretty_print for unknown message types
        msg.pretty_print()


def get_multiline_input(prompt: str = "You: ") -> str:
    """
    Get multiline input from user.
    - Single line: type and press Enter
    - Multiple lines: keep typing, press Enter twice (empty line) to submit
    """
    print(prompt, end="", flush=True)
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
    print("🤖 AI Coding Agent Ready.")
    print("   Type 'exit' to quit.")
    print("   For multiline input, press Enter twice to submit.\n")
    
    # Maintain conversation history for multi-turn conversations
    messages = []
    
    while True:
        try:
            user_input = get_multiline_input("\nYou: ")
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
            
            # Add user message to history
            messages.append(("user", user_input))
            
            # Track which messages we've already printed
            printed_count = 0
            
            async for chunk in agent.astream({
                "messages": messages
            }, stream_mode="values"):
                # Print all new messages (intermediate steps)
                all_messages = chunk["messages"]
                for msg in all_messages[printed_count:]:
                    print_message(msg)
                printed_count = len(all_messages)
            
            # Update messages with the final state (includes all AI responses and tool calls)
            messages = chunk["messages"]
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())