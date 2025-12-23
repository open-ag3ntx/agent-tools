from base.settings import settings
from langchain_core.tools import StructuredTool
from base.models import SkillToolResponse
from typing import Annotated


async def call_skill(
    skill_name: Annotated[str, "The name of the skill to be called"],
) -> SkillToolResponse:
    
    # Implementation will be handled by the agent framework
    return SkillToolResponse(
        skill_name=skill_name,
    )

description = f""""
    Execute a skill within the main conversation

    <skills_instructions>
    When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

    How to use skills:
    - Invoke skills using this tool with the skill name only (no arguments)
    - When you invoke a skill, you will see <command-message>The {{name}} skill is loading</command-message>
    - The skill's prompt will expand and provide detailed instructions on how to complete the task
    - Examples:
    - `skill: pdf` - invoke the pdf skill
    - `skill: xlsx` - invoke the xlsx skill
    - `skill: ms-office-suite:pdf` - invoke using fully qualified name

    Important:
    - Only use skills listed in <available_skills> below
    - Do not invoke a skill that is already running
    - Do not use this tool for built-in CLI commands (like /help, /clear, etc.)
    </skills_instructions>

    <available_skills>
    {settings.default_skills_directory} contains the following skills:
    </available_skills>

"""


call_skill_tool: StructuredTool = StructuredTool.from_function(
    func=call_skill,
    name="skill",
    description=description
)