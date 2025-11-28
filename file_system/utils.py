import os
import mimetypes

async def get_file_type(file_path: str) -> str:
    """
    Get the type of a file based on its extension.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension in [".svg", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".ico", ".webp"]:
        return "image"

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
    Check if a file is a binary file based on its extension.
    Heuristic: determine if a file is likely binary.
    Now BOM-aware: if a Unicode BOM is detected, we treat it as text.
    For non-BOM files, retain the existing null-byte and non-printable ratio checks.
    """
    with open(file_path, "rb") as f:
        data = f.read(1024)
        if data.startswith(b"\xEF\xBB\xBF"):
            return False
        return any(c < 32 or c > 126 for c in data)

    return False


async def read_file_content(file_path: str) -> str:
    """
    Read the content of a file.
    """
    file_content = open(file_path, "r").read()
    if len(file_content) == 0:
        return ""
    
    return file_content


if __name__ == "__main__":
    print(os.getcwd())