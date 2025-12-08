import asyncio
import json
from base.settings import settings
from bash.tools.grep import grep

if __name__ == "__main__":
    result = asyncio.run(grep(
        pattern="waterLevel",
        path='/Users/krishnakorade/Developer/osp/agent-tools/test/index.html',
        output_mode="content",
        n=True,
        multiline=True,
        offset=0,
        A=10,
        B=10,
        C=10,
        head_limit=1000,
    ))
    print(json.dumps(result.model_dump(), indent=4))