import os
import mimetypes

async def get_file_type(file_path: str) -> str:
    """
    Get the type of a file based on its extension.
    """
    # check if the file is a directory
    if os.path.isdir(file_path):
        return "directory"

    # get the extension of the file
    extension = os.path.splitext(file_path)[1].lower()

    if extension in [".svg", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".ico", ".webp"]:
        return "image"
    
    if extension in [".ts", ".mts", ".cts"]:
        return "text"
    
    mime_type = mimetypes.guess_type(file_path)[0]
    
    # If the mime type is not None, return the type of the file
    if mime_type is not None:
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("text/"):
            return "text"
        elif mime_type.startswith("application/pdf"):
            return "pdf"

    # check if the file is a binary file
    if await is_binary_file(file_path):
        return "binary"
    
    return "text"



async def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is a binary file based on its content.
    Heuristic: determine if a file is likely binary.
    Now BOM-aware: if a Unicode BOM is detected, we treat it as text.
    For non-BOM files, check for null bytes and high ratio of non-printable characters.
    """
    # Common text control characters that are allowed
    TEXT_CHARS = frozenset({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    
    with open(file_path, "rb") as f:
        data = f.read(1024)
        
        # Empty file is text
        if not data:
            return False
            
        # UTF-8 BOM means text
        if data.startswith(b"\xEF\xBB\xBF"):
            return False
        
        # UTF-16 BOM means text
        if data.startswith(b"\xFF\xFE") or data.startswith(b"\xFE\xFF"):
            return False
        
        # Null bytes are a strong indicator of binary
        if b'\x00' in data:
            return True
        
        # Check if most characters are printable/text
        non_text_chars = sum(1 for c in data if c not in TEXT_CHARS)
        # If more than 30% non-text characters, likely binary
        return (non_text_chars / len(data)) > 0.30


async def read_file_content(file_path: str) -> str:
    """
    Read the content of a file.
    """
    file_content = open(file_path, "r").read()
    if len(file_content) == 0:
        return ""
    
    return file_content


async def normalize_newlines(file_content: str) -> str:
    """
    Normalize the newlines in a file content.
    """
    return file_content.replace('\r\n', '\n')


async def safe_replace(file_content: str, old_content: str, new_content: str, replace_all: bool | None = True) -> str:
    """
    Safely replace the old content with the new content in a file content.
    
    Args:
        file_content: The content of the file
        old_content: The content to replace
        new_content: The content to replace with
        replace_all: If True, replace all occurrences. If False, replace only the first occurrence.
    """
    if old_content == '' or old_content not in file_content:
        return file_content

    if replace_all:
        return file_content.replace(old_content, new_content)
    else:
        # Replace only the first occurrence
        return file_content.replace(old_content, new_content, 1)


async def write_file_content(file_path: str, file_content: str) -> None:
    """
    Write the content of a file.
    """
    # TODO whats is the best way to write a file in a safe way?

    with open(file_path, "w") as file:
        file.write(file_content)


def get_file_extension(file_name: str) -> str:
    """
    Get the extension of a file.
    """
    return os.path.splitext(file_name)[1].lower()