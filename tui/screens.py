from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, TextArea, Button, Static, Label, Checkbox, RadioButton, RadioSet
from textual.containers import VerticalScroll, Vertical, Horizontal, Grid
from textual.events import Key
from rich.console import RenderableType

from tui.widgets import ChatMessage, ToolOutput, AgentStatus
from base.models import AskQuestionRequest

class QuestionModal(ModalScreen[dict[str, str]]):
    """A modal to ask the user a question."""
    
    CSS = """
    QuestionModal {
        align: center middle;
    }
    
    #dialog {
        padding: 0 1;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }
    
    .question-header {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }
    
    .question-text {
        margin-bottom: 1;
    }
    
    .option-description {
        color: $text-muted;
        margin-left: 2;
        margin-bottom: 1;
    }
    
    #buttons {
        width: 100%;
        align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, questions: list[AskQuestionRequest], **kwargs) -> None:
        super().__init__(**kwargs)
        self.questions = questions
        self.answers = {}
        self.current_question_index = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("User Input Required", classes="question-header")
            
            # We will mount the specific question widgets dynamically
            with Vertical(id="question-container"):
                pass
                
            with Horizontal(id="buttons"):
                yield Button("Submit", id="submit-answer", variant="primary")

    def on_mount(self) -> None:
        self.show_question(0)

    def show_question(self, index: int) -> None:
        if index >= len(self.questions):
            self.dismiss(self.answers)
            return
            
        self.current_question_index = index
        question = self.questions[index]
        
        container = self.query_one("#question-container", Vertical)
        container.remove_children()
        
        container.mount(Label(f"[{index+1}/{len(self.questions)}] {question.header}:", classes="message-role"))
        container.mount(Static(question.question, classes="question-text"))
        
        if question.multi_select:
            # Checkboxes
            for idx, option in enumerate(question.options):
                container.mount(Checkbox(option.label, id=f"opt_{idx}", value=False))
                container.mount(Label(option.description, classes="option-description"))
        else:
            # Radio buttons
            with RadioSet(id="radio-set"):
                for idx, option in enumerate(question.options):
                    container.mount(RadioButton(option.label, id=f"opt_{idx}"))
                    container.mount(Label(option.description, classes="option-description"))
                    
        # Always allow custom input (Other)
        container.mount(Label("Other (Custom Answer):", classes="message-role"))
        container.mount(TextArea(id="custom-answer", show_line_numbers=False, height=3))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-answer":
            self.save_answer_and_next()

    def save_answer_and_next(self) -> None:
        question = self.questions[self.current_question_index]
        custom_answer = self.query_one("#custom-answer", TextArea).text.strip()
        
        selected_labels = []
        
        if question.multi_select:
            for idx, option in enumerate(question.options):
                checkbox = self.query_one(f"#opt_{idx}", Checkbox)
                if checkbox.value:
                    selected_labels.append(option.label)
        else:
            radio_set = self.query_one("#radio-set", RadioSet)
            if radio_set.pressed_index is not None:
                selected_labels.append(question.options[radio_set.pressed_index].label)
        
        final_answer = ""
        if custom_answer:
            final_answer = custom_answer
        elif selected_labels:
            final_answer = ", ".join(selected_labels)
            
        self.answers[question.header] = final_answer
        self.show_question(self.current_question_index + 1)


class MainScreen(Screen):
    """The main screen for the Agent Chat."""

    CSS = """
    MainScreen {
        layers: base overlay;
    }

    #chat-container {
        height: 1fr;
        border: solid green;
        overflow-y: auto;
        
    }

    #input-container {
        height: auto;
        max-height: 20%;
        dock: bottom;
        border-top: solid white;
        padding: 1;
    }

    TextArea {
        height: auto;
        min-height: 3;
        max-height: 10;
    }
    
    .message-user {
        background: $primary-darken-3;
        padding: 1;
        margin: 1;
    }
    
    .message-ai {
        background: $secondary-darken-3;
        padding: 1;
        margin: 1;
    }
    
    .message-role {
        text-style: bold;
        color: $accent;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield AgentStatus(id="agent-status")
        
        with VerticalScroll(id="chat-container"):
            yield ChatMessage("ai", "AI Coding Agent Ready. Type your request below.")
        
        with Vertical(id="input-container"):
            yield TextArea(id="user-input", show_line_numbers=False)
            yield Button("Send", id="send_button", variant="primary")
            
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#user-input").focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            await self.submit_input()

    async def action_submit(self) -> None:
        await self.submit_input()

    async def submit_input(self) -> None:
        text_area = self.query_one("#user-input", TextArea)
        text = text_area.text.strip()
        if not text:
            return
        
        text_area.clear()
        
        # Display user message
        chat_container = self.query_one("#chat-container", VerticalScroll)
        chat_container.mount(ChatMessage("user", text))
        chat_container.scroll_end(animate=True)
        
        # Notify the app (controller)
        await self.app.on_user_input(text)

    def append_message(self, role: str, content: str) -> ChatMessage:
        chat_container = self.query_one("#chat-container", VerticalScroll)
        message = ChatMessage(role, content)
        chat_container.mount(message)
        chat_container.scroll_end(animate=True)
        return message

    def append_tool_output(self, tool_name: str, output: str | RenderableType) -> None:
        chat_container = self.query_one("#chat-container", VerticalScroll)
        tool_widget = ToolOutput(tool_name, output)
        chat_container.mount(tool_widget)
        chat_container.scroll_end(animate=True)

    def set_agent_status(self, status: str) -> None:
        self.query_one("#agent-status", AgentStatus).set_status(status)
