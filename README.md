# 🛠️ Agent Tools

A community-driven collection of tools for LangChain/LangGraph agents. Build smarter agents by plugging in ready-to-use tools or contribute your own.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-green.svg)](https://python.langchain.com/)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-tools.git
cd agent-tools

# Create virtual environment with uv
uv venv
source .venv/bin/activate
# Install dependencies
uv pip install -r todo/requirements.txt
# Set up environment variables
cp .env.example .env
# Add your API keys to .env
```

## Available Tools

| Category | Tools | Description | Status |
|----------|-------|-------------|--------|
| [**Bash & Shell**](./bash/) | `bash`, `glob`, `grep` | Execute shell commands and perform advanced searches | ✅ Ready |
| [**File System**](./file_system/) | `read_file`, `write_file`, `edit_file` | Robust file manipulation with safety checks | ✅ Ready |
| [**Todo Manager**](./todo/) | `create_todo`, `list_todos`, `update_todo` | Track progress during multi-step agent tasks | ✅ Ready |
| [**Interactive**](./interactive/) | `ask_question` | Human-in-the-loop interaction for clarifying questions | ✅ Ready |
| [**Subagents**](./subagents/) | `subagent` | Delegate complex tasks to specialized sub-agents | ✅ Ready |
| [**Skills**](./skills/) | - | Extensible framework for adding custom capabilities | 🚧 Beta |

## Usage

### Using the Tools

The tools are designed to be used with LangChain or LangGraph agents. Here's how to initialize a basic agent with our tool collection:

```python
from base.models import ToolCollection
from bash.tools import BASH_TOOLS
from file_system.tools import FILE_SYSTEM_TOOLS
from todo.tools import TODO_TOOLS

# Combine toolsets
all_tools = BASH_TOOLS + FILE_SYSTEM_TOOLS + TODO_TOOLS

# Or use the ToolCollection to load everything
# collection = ToolCollection().load_all()
```

### Example: File Editing
```python
# The agent can intelligently edit files instead of rewriting them
edit_file(
    file_path="/path/to/script.py",
    old_content="def old_func():\n    pass",
    new_content="def new_func():\n    print('Hello World')",
)
```

## Contributing

We welcome contributions! Here's how to add your own tools:

### Adding a New Tool

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/agent-tools.git
   cd agent-tools
   ```

2. **Create a new tool directory**
   ```bash
   mkdir my_tool
   cd my_tool
   ```

3. **Structure your tool**
   ```
   my_tool/
   ├── __init__.py
   ├── tools.py          # Your tool implementations
   ├── prompt.md         # System prompt for the agent
   └── requirements.txt  # Tool-specific dependencies
   ```

4. **Implement your tools** in `tools.py`:
   ```python
   from langchain_core.tools import tool
   from typing import Annotated

   @tool
   def my_awesome_tool(
       param: Annotated[str, "Description of the parameter"]
   ) -> str:
       """Clear docstring explaining what the tool does.
       
       Include:
       - When to use this tool
       - What it returns
       - Example usage
       """
       # Your implementation
       return "result"

   MY_TOOLS = [my_awesome_tool]
   ```

5. **Write a system prompt** in `prompt.md` explaining how the agent should use your tools

6. **Submit a Pull Request**

### Tool Guidelines

- ✅ Use clear, descriptive tool names
- ✅ Write comprehensive docstrings (agents read these!)
- ✅ Use `Annotated` types for parameter descriptions
- ✅ Include a `prompt.md` with usage guidelines
- ✅ Add tool-specific dependencies to a local `requirements.txt`
- ✅ Include example usage in your PR description

### Pull Request Process

1. Ensure your tool works with the latest LangChain/LangGraph
2. Update the README table with your new tool
3. Add any new dependencies
4. Submit PR with a clear description and example usage

## Project Structure

```
agent-tools/
├── agent.py            # Example agent implementation
├── base/               # Shared base classes and utilities
├── bash/               # Shell execution & search tools (grep, glob)
├── file_system/        # File I/O and targeted editing tools
├── interactive/        # Human-in-the-loop interaction tools
├── skills/             # Reusable agent skill modules
├── subagents/          # Sub-agent delegation tools
└── todo/               # Multi-step task tracking tools
```

## Environment Variables

Create a `.env` file with your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
# Add other provider keys as needed
```

## Requirements

- Python 3.10+
- LangChain 1.0+
- LangGraph 1.0+

## License

MIT License - see [LICENSE](LICENSE) for details.

## Show Your Support

Give a ⭐ if this project helped you build better agents!

---

**Built with ❤️ by the community**

