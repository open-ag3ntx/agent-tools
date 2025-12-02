import datetime
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate, prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
import os

try:
    from rich.console import Console
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

from file_system.settings import settings as file_system_settings
from file_system.tools.write_file import write_file
from file_system.tools.read_file import read_file
from file_system.tools.edit_file import edit_file
from todo.tools import list_todos
from todo.tools import update_todo
from todo.tools import delete_todo
from todo.tools import create_todo
from command_line.tools.execute_command import execute_command

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    api_key=os.getenv("GOOGLE_API_KEY")
)

tools = [
    read_file,
    edit_file,
    write_file,
    create_todo,
    list_todos,
    update_todo,
    delete_todo,
    execute_command,
]

def create_prompt():
    prompt_template = PromptTemplate.from_template(
        """{agent_prompt}
        
        {file_system_prompt}
        
        {command_line_prompt}
        
        {todo_prompt}
        
        Information about the environment you are working in:
        Current directory: {current_directory}
        """
    )
    with open("agent-prompt.md", "r") as f:
        agent_prompt = f.read()
    with open("file_system/prompt.md", "r") as f:
        file_system_prompt = f.read()
    with open("command_line/prompt.md", "r") as f:
        command_line_prompt = f.read()
    with open("todo/prompt.md", "r") as f:
        todo_prompt = f.read()
    return prompt_template.format(
        agent_prompt=agent_prompt, 
        file_system_prompt=file_system_prompt, 
        command_line_prompt=command_line_prompt,
        todo_prompt=todo_prompt,
        current_directory=file_system_settings.present_test_directory,
    )


agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=create_prompt()
)


def print_message(msg):
    """Pretty print a message with markdown formatting for text content."""
    if isinstance(msg, HumanMessage):
        print("================================ Human Message =================================")
        print(msg.content)
    elif isinstance(msg, ToolMessage):
        print("================================= Tool Message =================================")
        print(f"Name: {msg.name}")
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
                        if RICH_AVAILABLE and text:
                            console.print(Markdown(text))
                        elif text:
                            print(text)
                    elif isinstance(block, str):
                        if RICH_AVAILABLE:
                            console.print(Markdown(block))
                        else:
                            print(block)
            elif isinstance(content, str) and content:
                if RICH_AVAILABLE:
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