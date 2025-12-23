from idna.idnadata import scripts
from markdown_it.rules_block import reference

from pydantic import BaseModel
from typing import Optional
from typing import Literal
from typing import Annotated


class BashToolResult(BaseModel):
    success: bool = True
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    command: Optional[str] = None
    timed_out: bool = False
    run_in_background: bool = False
    process_id: Optional[int] = None

class BaseToolResult(BaseModel):
    success: bool = True
    error: Optional[str] = None
    content: Optional[str] = None

class TodoItem(BaseModel):
    id: int
    task_group: str
    title: str
    status: Literal["pending", "completed", "cancelled"] = "pending"


class GlobToolResult(BaseToolResult):
    files: list[str] = []
    total_files: int = 0
    skipped_files: int = 0


class GrepToolResult(BaseToolResult):
    lines: list[str] = []
    files: list[str] = []
    counts: int = 0


class AskQuestionOption(BaseModel):
    label: Annotated[str, "The display text for this option that the user will see and select. Should be concise (1-5 words) and clearly describe the choice."]
    description: Annotated[str, "Explanation of what this option means or what will happen if chosen. Useful for providing context about trade-offs or implications."]


class AskQuestionRequest(BaseModel):
    question: Annotated[str, "The complete question to ask the user. Should be clear, specific, and end with a question mark. Example: \"Which library should we use for date formatting?\" If multiSelect is true, phrase it accordingly, e.g. \"Which features do you want to enable?\""]
    header: Annotated[str, "Very short label displayed as a chip/tag (max 12 chars). Examples: \"Auth method\", \"Library\", \"Approach\"."]
    options: Annotated[list[AskQuestionOption], "The available choices for this question. Must have 2-4 options. Each option should be a distinct, mutually exclusive choice (unless multiSelect is enabled). There should be no 'Other' option, that will be provided automatically."]
    multi_select: Annotated[bool, "Set to true to allow the user to select multiple options instead of just one. Use when choices are not mutually exclusive."]


class SkillToolResponse(BaseModel):
    skill_name: Annotated[str, "The name of the skill that was called."]
    instructions: Annotated[Optional[str], "Any special instructions or notes related to the skill execution."] = None
    references: Annotated[Optional[list[str]], "List of reference links or documents relevant to the skill execution."] = None
    assets: Annotated[Optional[dict], "Any assets (files, data) produced or used by the skill."] = None
    scripts: Annotated[Optional[dict], "Any scripts or code snippets generated or utilized by the skill."] = None