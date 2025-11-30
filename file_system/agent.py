from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import TODO_TOOLS
from dotenv import load_dotenv
import os
import json

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    api_key=os.getenv("GOOGLE_API_KEY")
)

agent = create_agent(
    model=model,
    tools=TODO_TOOLS,
    system_prompt=open("todo/prompt.md").read()
)

for chunk in agent.stream({
    "messages": [("user", "Please build a web app with next.js, tailwind css and shadcn/ui and deploy it to vercel")]
}, stream_mode="values"):
    chunk["messages"][-1].pretty_print()