import asyncio
from bash.tools import glob
from base.settings import settings

async def main():
    result = await glob("**/*.js", settings.present_test_directory)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())