import datetime
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate, prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

from file_system.settings import settings as file_system_settings
from file_system.tools.write_file import write_file
from file_system.tools.read_file import read_file
from file_system.tools.edit_file import edit_file
from todo.tools import list_todos
from todo.tools import update_todo
from todo.tools import delete_todo
from todo.tools import create_todo

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
]

def create_prompt():
    prompt_template = PromptTemplate.from_template(
        """{agent_prompt}
        
        {file_system_prompt}
        
        {todo_prompt}
        
        Information about the environment you are working in:
        Current directory: {current_directory}
        """
    )
    with open("agent-prompt.md", "r") as f:
        agent_prompt = f.read()
    with open("file_system/prompt.md", "r") as f:
        file_system_prompt = f.read()
    with open("todo/prompt.md", "r") as f:
        todo_prompt = f.read()
    return prompt_template.format(
        agent_prompt=agent_prompt, 
        file_system_prompt=file_system_prompt, 
        todo_prompt=todo_prompt,
        current_directory=file_system_settings.present_test_directory,
    )


agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=create_prompt()
)
# create a simple HTTP server in Python using the FastAPI framework, add routes for greetings and health checks

async def main():
    print("🤖 AI Coding Agent Ready. Type 'exit' to quit.\n")
    
    # Maintain conversation history for multi-turn conversations
    messages = []
    
    while True:
        try:
            user_input = input("\nYou: ")
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
                    msg.pretty_print()
                printed_count = len(all_messages)
            
            # Update messages with the final state (includes all AI responses and tool calls)
            messages = chunk["messages"]
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())