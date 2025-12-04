import asyncio
import json
from base.settings import settings
from bash.tools import glob

if __name__ == "__main__":
    result = asyncio.run(glob("*/**", path=settings.present_test_directory))
    print(json.dumps(result.model_dump(), indent=4))