from textual.app import ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Static, Collapsible, Label
from rich.markdown import Markdown
from rich.console import RenderableType

class ChatMessage(Container):
    """A widget to display a message in the chat."""

    def __init__(self, role: str, content: str | RenderableType, **kwargs) -> None:
        super().__init__(**kwargs)
        self.role = role
        self.content = content
        if role == "user":
            self.add_class("message-user")
        else:
            self.add_class("message-ai")

    def compose(self) -> ComposeResult:
        yield Label(f"{self.role.capitalize()}:", classes="message-role")
        if isinstance(self.content, str):
            yield Static(Markdown(self.content), classes="message-content")
        else:
            yield Static(self.content, classes="message-content")

class ToolOutput(Container):
    """A widget to display tool output in a collapsible container."""

    def __init__(self, tool_name: str, output: str | RenderableType, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.output = output

    def compose(self) -> ComposeResult:
        title = f"🛠️ Tool: {self.tool_name}"
        
        renderable = self.output
            
        yield Collapsible(
            Static(renderable),
            title=title,
            collapsed=True
        )

class AgentStatus(Static):
    """Widget to show what the agent is currently doing."""
    
    def on_mount(self) -> None:
        self.update("Ready.")

    def set_status(self, status: str) -> None:
        self.update(f"🤖 {status}")
