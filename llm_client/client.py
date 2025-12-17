from dotenv import load_dotenv
from typing import Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from file_system.tools import read_file, edit_file, write_file
from todo.tools import list_todos, update_todo, create_todo
from bash.tools import bash, glob, grep
from interactive.tools.ask_question import ask_question
from subagents.tools.subagent import subagent
import os
from loguru import logger



class LLMClient:

    __llm = None

    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        model_provider = os.getenv("MODEL_PROVIDER", "google").lower()
        model = os.getenv("MODEL_NAME", "gemini-2.5-flash")

        if model_provider == "google":
            self.__llm = ChatGoogleGenerativeAI(
                model=model,
                api_key=os.getenv("GOOGLE_API_KEY_V2"),
            )
        elif model_provider == "openrouter":
            self.__llm = ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENROUTER_KEY"),
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            raise ValueError("Unsupported model provider")
        logger.info(f'Initilised LLMClient with provider {model_provider} model {model}')
    @property
    def llm(self):
        return self.__llm
    
    def get_new_instance(self):
        
        return LLMClient().llm

    def get_file_system_tools(self):
        return [read_file.read_file, edit_file.edit_file, write_file.write_file]
    
    def get_todo_tools(self):
        return [create_todo, list_todos, update_todo]
    
    def get_bash_tools(self):
        return [bash, glob, grep]
    
    def get_interactive_tools(self):
        return [ask_question]
    
    def get_subagent_tool(self):
        return [subagent]


client = LLMClient()

        