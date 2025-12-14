

from typing import Annotated
from typing import Optional

from base.models import AskQuestionRequest


async def ask_question(
    questions: Annotated[list[AskQuestionRequest], "The questions to ask the user (1-4 questions)"],
) -> dict[str, str]:
    """
    Use this tool when you need to ask the user questions during execution. This allows you to:
    1. Gather user preferences or requirements
    2. Clarify ambiguous instructions
    3. Get decisions on implementation choices as you work
    4. Offer choices to the user about what direction to take.

    Usage notes:
    - Users will always be able to select \"Other\" to provide custom text input
    - Use multiSelect: true to allow multiple answers to be selected for a question

    """

    for question in questions:
        print("================================= User Question =================================")
        print(f"Header: {question.header}")
        print(f"Question: {question.question}")
        print("Options:")
        for idx, option in enumerate(question.options):
            print(f"  {idx + 1}. {option.label} - {option.description}")
        if question.multi_select:
            print("  You may select multiple options (comma separated).")
        print("  0. Other - Provide a custom answer.")
        chosen = input("Please enter the number(s) of your choice: ")
        chosen_indices = [int(x.strip()) for x in chosen.split(",") if x.strip().isdigit()]
        answers = {}
        for idx in chosen_indices:
            if idx == 0:
                custom_answer = input("Please enter your custom answer: ")
                answers[question.header] = custom_answer
            elif 1 <= idx <= len(question.options):
                selected_option = question.options[idx - 1]
                answers[question.header] = selected_option.label
            else:
                print(f"Invalid choice: {idx}")
    return answers