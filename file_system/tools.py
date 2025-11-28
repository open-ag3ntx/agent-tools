from typing import Annotated


def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    limit: Annotated[int, "The maximum number of lines to read"] = 2000,
    offset: Annotated[int, "The number of lines to skip"] = 0
) -> str:
    """"""
    