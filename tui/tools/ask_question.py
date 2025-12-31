from typing import Annotated
from base.models import AskQuestionRequest
from tui.globals import get_app

async def ask_question(
    questions: Annotated[list[AskQuestionRequest], "The questions to ask the user (1-4 questions)"],
) -> dict[str, str]:
    """
    Use this tool when you need to ask the user questions during execution.
    This version delegates to the Textual TUI to show a modal.
    """
    app = get_app()
    return await app.ask_user(questions)
