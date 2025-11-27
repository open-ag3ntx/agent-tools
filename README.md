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

| Tool | Description | Status |
|------|-------------|--------|
| [Todo Manager](./todo/) | Track progress during multi-step agent tasks | ✅ Ready |

## Usage

### Using the Todo Tools

```python
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from todo.tools import TODO_TOOLS

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

agent = create_agent(
    model=model,
    tools=TODO_TOOLS,
    system_prompt=open("todo/prompt.md").read()
)

for chunk in agent.stream({
    "messages": [("user", "Build a Next.js app with Tailwind")]
}, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
```

### Available Todo Operations

- `create_todo(title, task_group)` - Create a trackable task
- `list_todos(task_group)` - View all tasks in a group
- `update_todo(task_group, todo_id, status)` - Mark as completed/cancelled
- `delete_todo(task_group, todo_id)` - Remove a task

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
├── README.md
├── .env.example
├── .gitignore
├── todo/                    # Todo management tools
│   ├── __init__.py
│   ├── agent.py            # Example agent implementation
│   ├── tools.py            # Tool definitions
│   ├── prompt.md           # System prompt
│   └── requirements.txt    # Dependencies
└── your_tool/              # Your contribution here!
    ├── __init__.py
    ├── tools.py
    ├── prompt.md
    └── requirements.txt
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

