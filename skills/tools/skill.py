from base.settings import settings
from langchain_core.tools import StructuredTool
from base.models import SkillToolResponse
from typing import Annotated
import os
import yaml

__skills: list[dict] = []

async def call_skill(
    skill_name: Annotated[str, "The name of the skill to be called"],
) -> SkillToolResponse:
    
    skill = next((s for s in __skills if s.get('name') == skill_name), None)
    if not skill:   
        return SkillToolResponse(
            exists=False,
            skill_name=skill_name,
        )
    skill_content: str | None = None
    with open(os.path.join(settings.default_skills_directory, skill_name, 'SKILLS.md'), 'r', encoding='utf-8-sig') as f:
        skill_content = f.read()
    dirs = os.listdir(os.path.join(settings.default_skills_directory, skill_name))
    references = []
    scripts = {}
    assets = {}
    for d in dirs:
        if d == 'references':
            references = os.listdir(os.path.join(settings.default_skills_directory, skill_name, d))
        elif d == 'scripts':
            scripts = {f: os.path.join(settings.default_skills_directory, skill_name, d, f) for f in os.listdir(os.path.join(settings.default_skills_directory, skill_name, d))}
        elif d == 'assets':
            assets = {f: os.path.join(settings.default_skills_directory, skill_name, d, f) for f in os.listdir(os.path.join(settings.default_skills_directory, skill_name, d))}

    return SkillToolResponse(
        skill_name=skill_name,
        exists=True,
        instructions=skill_content,
        references=references,
        scripts=scripts,
        assets=assets
    )

def extract_front_matter(file_path) -> dict | None:
    """Extract YAML front matter from markdown file."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    if not lines or lines[0].strip() != '---':
        return None
    
    yaml_lines = []
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            yaml_content = ''.join(yaml_lines)
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                return None
        yaml_lines.append(lines[i])
    
    return None


def get_skill_tool_description(skills: list[dict]) -> str:
    description = f"""
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
        {
            ''.join([f"Name: {skill.get('name', 'unknown_skill')}\n Description: {skill.get('description', 'No description')}\n" for skill in skills])
        }
        </available_skills>

    """
    return description


def setup_skills_tool() -> StructuredTool:
    skills: list[dict] = []
    for d in os.listdir(settings.default_skills_directory):
        if d.startswith('.'):
            continue
        file_path = os.path.join(settings.default_skills_directory, d, 'SKILLS.md')
        if os.path.isfile(file_path):
            data = extract_front_matter(file_path)
            if data:
                skills.append(data)
    global __skills
    __skills = skills
    return StructuredTool.from_function(
        func=call_skill,
        name="skill",
        description=get_skill_tool_description(skills)
    )
