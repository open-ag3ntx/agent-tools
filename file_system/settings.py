import os
from pydantic_settings import BaseSettings

class FileSystemSettings(BaseSettings):
    file_size_limit: int = 10 * 1024 * 1024 # 100MB
    max_lines_to_read: int = 2000
    max_length_of_line: int = 2000

    # present working directory of the user
    present_working_directory: str = os.getcwd()


settings = FileSystemSettings()