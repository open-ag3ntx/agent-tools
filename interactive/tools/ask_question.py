

from typing import Annotated
from typing import Optional


async def ask_question(
    question: Annotated[str, "The question to ask"],
    options: Annotated[Optional[list[str]], "The options to choose from"],
) -> str:
    """
    Ask a question and return the answer.
    """
    return "Answer to the question"