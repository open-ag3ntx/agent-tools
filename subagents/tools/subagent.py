from typing import Annotated
from langchain.messages import SystemMessage
from langchain.agents import create_agent


async def subagent(
    subagent_type: Annotated[str, "The type of agent to launch, which determines the tools and capabilities it has access to. For example, a 'code-reviewer' agent would have access to code analysis tools and would be expected to review code, while a 'greeting-responder' agent would have access to a joke database and would be expected to respond to greetings with jokes."],
    description: Annotated[str, "A short (3-5 word) description of the task the"],
    prompt: Annotated[str, "The task for the agent to perform autonomously"],
) -> str:
    """
    Launch a new agent to handle complex, multi-step tasks autonomously. 

    The Task tool launches specialized agents (subprocesses) that autonomously handle complex tasks. Each agent type has specific capabilities and tools available to it.

    When NOT to use the Task tool:
    - If you want to read a specific file path, use the Read or Glob tool instead of the Task tool, to find the match more quickly
    - If you are searching for a specific class definition like \"class Foo\", use the Glob tool instead, to find the match more quickly
    - If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Task tool, to find the match more quickly
    - Other tasks that are not related to the agent descriptions above


    Usage notes:
    - Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
    - When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
    - Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
    - Agents with \"access to current context\" can see the full conversation history before the tool call. When using these agents, you can write concise prompts that reference earlier context (e.g., \"investigate the error discussed above\") instead of repeating information. The agent will receive all prior messages and understand the context.
    - The agent's outputs should generally be trusted
    - Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent
    - If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.
    - If the user specifies that they want you to run agents \"in parallel\", you MUST send a single message with multiple Task tool use content blocks. For example, if you need to launch both a code-reviewer agent and a test-runner agent in parallel, send a single message with both tool calls.

    Example usage:

    <example_agent_descriptions>
    \"code-reviewer\": use this agent after you are done writing a signficant piece of code
    \"greeting-responder\": use this agent when to respond to user greetings with a friendly joke
    </example_agent_description>

    <example>
    user: \"Please write a function that checks if a number is prime\"
    assistant: Sure let me write a function that checks if a number is prime
    assistant: First let me use the Write tool to write a function that checks if a number is prime
    assistant: I'm going to use the Write tool to write the following code:
    <code>
    function isPrime(n) {
    if (n <= 1) return false
    for (let i = 2; i * i <= n; i++) {
        if (n % i === 0) return false
    }
    return true
    }
    </code>
    <commentary>
    Since a signficant piece of code was written and the task was completed, now use the code-reviewer agent to review the code
    </commentary>
    assistant: Now let me use the code-reviewer agent to review the code
    assistant: Uses the Task tool to launch the code-reviewer agent 
    </example>

    """
    from llm_client.client import client
    llm = client.get_new_instance()
    subagent_tools = []
    subagent_tools.extend(client.get_file_system_tools())
    subagent_tools.extend(client.get_todo_tools())
    subagent_tools.extend(client.get_bash_tools())
    subagent_tools.extend(client.get_interactive_tools())

    subagent = create_agent(
        model=llm,
        tools=subagent_tools,
        system_prompt="""
            You are an autonomous sub-agent launched to perform a specific task. You have access to various tools to help you complete your task.
            Your goal is to complete the task assigned to you as effectively as possible using the available tools.
            When you are done, return the result of your task so main agent can act on it.
        """

    )
    config = {"configurable": {"thread_id": "1"}} 
    
    result = await subagent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": (f"You have been assigned a new task to complete autonomously\n\n"
                    f"Task Description: {description}\n\n"
                    f"Task Prompt: {prompt}")
                }
            ]
        },
        config=config
    )

    return result['messages'][-1].content

