import asyncio
from ag3tools.core.registry import invoke_tool_async


def test_invoke_tool_async():
    async def run():
        res = await invoke_tool_async("find_docs", technology="langgraph")
        assert getattr(res, "url", None)
    asyncio.run(run())

