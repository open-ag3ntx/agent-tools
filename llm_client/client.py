from dotenv import load_dotenv
from typing import Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from file_system.tools import read_file, edit_file, write_file
from todo.tools import list_todos, update_todo, create_todo
from bash.tools import bash, glob, grep



class LLMClient:

    __llm = None

    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        model_provider = os.getenv("MODEL_PROVIDER", "google").lower()
        model = os.getenv("MODEL_NAME", "gemini-2.5-flash")

        if model_provider == "google":
            self.__llm = ChatGoogleGenerativeAI(
                model=model
            )
        elif model_provider == "openrouter":
            self.__llm = ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENROUTER_KEY"),
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            raise ValueError("Unsupported model provider")
    
    @property
    def llm(self):
        return self.__llm
    
    def get_new_instance(self):
        return LLMClient().llm


client = LLMClient()

        