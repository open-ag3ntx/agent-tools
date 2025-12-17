from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Footer
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.message import Message
from textual import events
from typing import List, Dict, Any
import asyncio
from rich.console import Console
from rich.markdown import Markdown
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from agent import agent


class AgentMessage(Message):
    """Custom message to handle agent responses."""
    def __init__(self, message: Dict[str, Any]) -> None:
        self.message = message
        super().__init__()


class AgentUI(App):
    """Terminal UI for the AI Coding Agent."""
    CSS = """
        Vertical {
            height: 100%;
            width: 100%;
        }
        
        #output {
            height: 80%;
            width: 100%;
            border: solid $primary;
            overflow-y: auto;
        }
        
        #input-container {
            height: 20%;
            width: 100%;
            border: solid $primary;
        }
        
        Input {
            width: 100%;
            height: 100%;
        }
        
        Footer {
            dock: bottom;
        }
    """
    
    messages: reactive[List[Dict[str, Any]]] = reactive([{"type": "system", "content": "Initializing agent..."}])
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Vertical(
            RichLog(id="output"),
            Horizontal(
                Input(placeholder="Type your message here...", id="user-input"),
                id="input-container"
            ),
            Footer()
        )
    
    def on_mount(self) -> None:
        """Initialize the UI."""
        self.query_one(RichLog).write("🤖 AI Coding Agent Ready.")
        self.query_one(RichLog).write("   Type 'exit' to quit.")
        self.query_one(RichLog).write("   For multiline input, press Enter twice to submit.\n")
        self.query_one("#user-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value
        input_widget = self.query_one("#user-input", Input)
        
        if user_input.lower() == "exit":
            self.exit()
            return
        
        if not user_input.strip():
            return
        
        # Display user input
        self.query_one(RichLog).write(f"[bold]You:[/bold] {user_input}")
        
        # Clear input
        input_widget.value = ""
        
        # Add user message to history in the correct format
        self.messages.append({"type": "human", "content": user_input})
        
        # Process agent response
        asyncio.create_task(self.process_agent_response())
    
    async def process_agent_response(self) -> None:
        """Process the agent's response asynchronously."""
        printed_count = 0
        async for chunk in agent.astream({"messages": self.messages}, stream_mode="values"):
            all_messages = chunk["messages"]
            for msg in all_messages[printed_count:]:
                self.post_message(AgentMessage(msg))
            printed_count = len(all_messages)
        
        # Update messages with the final state
        self.messages = chunk["messages"]
    
    def on_agent_message(self, message: AgentMessage) -> None:
        """Handle agent messages."""
        self.print_message(message.message)
    
    def print_message(self, msg: Dict[str, Any]) -> None:
        """Pretty print a message with markdown formatting for text content."""
        output = self.query_one(RichLog)
        
        if isinstance(msg, dict):
            msg_type = msg.get("type")
            content = msg.get("content", "")
            
            if msg_type == "human":
                output.write("================================ Human Message =================================")
                output.write(content)
            elif msg_type == "tool":
                output.write("================================= Tool Message =================================")
                output.write(content)
            elif msg_type == "ai":
                output.write("================================== AI Message ==================================")
                
                # Handle tool calls
                if "tool_calls" in msg:
                    output.write("Tool Calls:")
                    for tool_call in msg["tool_calls"]:
                        output.write(f"  {tool_call['name']} ({tool_call['id']})")
                        output.write(f"  Args:")
                        for key, value in tool_call["args"].items():
                            value_str = str(value)
                            if len(value_str) > 100:
                                value_str = value_str[:100] + "..."
                            output.write(f"    {key}: {value_str}")
                
                # Handle text content
                if content:
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                text = block.get('text', '')
                                if text:
                                    console = Console()
                                    console.print(Markdown(text))
                            elif isinstance(block, str):
                                output.write(block)
                    elif isinstance(content, str):
                        console = Console()
                        console.print(Markdown(content))
    
    def on_key(self, event: events.Key) -> None:
        """Handle key events for multiline input."""
        # Allow multiline input with Shift+Enter
        # Note: Textual's Key event does not directly expose modifier keys.
        # Instead, we can use the Input widget's built-in multiline support.
        pass


def run_tui():
    """Run the Terminal UI."""
    app = AgentUI()
    app.run()


if __name__ == "__main__":
    run_tui()