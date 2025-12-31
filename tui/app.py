import asyncio
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, BaseMessage
from langchain.agents import create_agent

from tui.screens import MainScreen, QuestionModal
from tui.globals import set_app
from tui.tools.ask_question import ask_question as tui_ask_question
from tui.widgets import ChatMessage

# Import existing core logic
from llm_client.client import client as llm_client
from base.settings import settings as file_system_settings
import datetime

# Import display helpers
from file_system.tools.read_file import display_read_file, get_read_file_tool_output
from file_system.tools.write_file import display_write_file
from file_system.tools.edit_file import display_edit_file
from bash.tools.bash import display_bash
from bash.tools.grep import display_grep
from bash.tools.glob import display_glob
from todo.tools.list_todos import display_list_todos
from todo.tools.update_todo import display_update_todo
from todo.tools.create_todo import display_create_todo


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

class AgentApp(App):
    """Textual App for the Agent."""

    CSS_PATH = None
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self):
        super().__init__()
        self.messages: List[BaseMessage] = []
        self.agent = None
        set_app(self)

    def on_mount(self) -> None:
        self.setup_agent()
        self.push_screen(MainScreen())

    def setup_agent(self):
        tools = [
            *llm_client.get_file_system_tools(),
            *llm_client.get_todo_tools(),
            *llm_client.get_bash_tools(),
            tui_ask_question, 
            *llm_client.get_subagent_tool(),
            *llm_client.get_skill_tool(),
        ]

        llm = llm_client.get_new_instance()
        
        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=create_prompt()
        )

    async def on_user_input(self, text: str) -> None:
        main_screen = self.query_one(MainScreen)
        main_screen.set_agent_status("Thinking...")
        
        self.messages.append(("user", text))
        self.run_worker(self.run_agent_loop(), exclusive=True)

    async def run_agent_loop(self):
        main_screen = self.query_one(MainScreen)
        accumulated_content = ""
        current_message_widget = main_screen.append_message("ai", "")
        
        final_messages = None
        
        try:
            async for event in self.agent.astream_events({
                "messages": self.messages
            }, version="v2"):
                kind = event["event"]
                data = event["data"]
                
                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk:
                        content = chunk.content
                        if content:
                            accumulated_content += content
                            current_message_widget.query_one(".message-content").update(accumulated_content)
                            current_message_widget.scroll_visible()
                            
                elif kind == "on_tool_start":
                    name = event["name"]
                    input_data = data.get('input', {})
                    
                    try:
                        match name:
                            case "read_file":
                                summary = display_read_file(**input_data)
                            case "write_file":
                                summary = display_write_file(**input_data)
                            case "edit_file":
                                summary = display_edit_file(**input_data)
                            case 'glob':
                                summary = display_glob(**input_data)
                            case 'grep':
                                summary = display_grep(**input_data)
                            case 'bash':
                                summary = display_bash(**input_data)
                            case 'create_todo': 
                                summary = display_create_todo(**input_data)
                            case 'update_todo':
                                summary = display_update_todo(**input_data)
                            case 'list_todos':
                                summary = display_list_todos(**input_data)
                    except Exception:
                        pass

                    main_screen.set_agent_status(f"Running {name}...")
                    
                elif kind == "on_tool_end":
                    name = event["name"]
                    tool_output = data.get("output")
                    if tool_output:
                        summary = f"Tool ({name}) Output"
                        if name == "read_file":
                             summary = get_read_file_tool_output(data)
                             # output is likely a Syntax object here if using helper, or raw dict
                             # get_read_file_tool_output returns a Syntax object!
                             main_screen.append_tool_output(name, summary)
                        else:
                            output_str = str(tool_output)
                            if hasattr(tool_output, 'content'):
                                 output_str = tool_output.content
                            elif hasattr(tool_output, 'stdout'):
                                 output_str = f"STDOUT:\n{tool_output.stdout}\nSTDERR:\n{tool_output.stderr}"
                            
                            main_screen.append_tool_output(name, output_str)
                
                elif kind == "on_chain_end":
                    if not data.get("parent_ids"):
                        output = data.get("output")
                        if isinstance(output, dict) and "messages" in output:
                            final_messages = output["messages"]

        except Exception as e:
            main_screen.append_message("system", f"Error: {e}")
        
        main_screen.set_agent_status("Ready")
        
        if final_messages:
            self.messages = final_messages
        else:
             if accumulated_content:
                self.messages.append(AIMessage(content=accumulated_content))

    async def ask_user(self, questions: List[Any]) -> Dict[str, str]:
        return await self.push_screen(QuestionModal(questions), wait_for_dismiss=True)

if __name__ == "__main__":
    app = AgentApp()
    app.run()
