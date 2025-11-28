from pydantic_settings import BaseSettings

class FileSystemConfig(BaseSettings):
    FILE_SIZE_LIMIT: int = 10 * 1024 * 1024 # 100MB
    MAX_LINES_TO_READ: int = 2000
    MAX_LENGTH_OF_LINE: int = 2000