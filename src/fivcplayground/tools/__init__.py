__all__ = [
    "setup_tools",
    "default_retriever",
    "default_loader",
    "Tool",
    "ToolsBundle",
    "ToolsConfig",
    "ToolsRetriever",
    "ToolsLoader",
]

from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator, List

from fivcplayground.utils import LazyValue
from fivcplayground.tools.types import (
    ToolsRetriever,
    ToolsConfig,
    ToolsLoader,
)
from fivcplayground.tools.types.backends import (
    Tool,
    ToolsBundle,
    get_tool_name,
)
from fivcplayground.tools.clock import clock
from fivcplayground.tools.calculator import calculator


def _load_retriever() -> ToolsRetriever:
    """Load and initialize the default tools retriever.

    This creates a ToolsRetriever and loads MCP tools from configured servers.
    """
    retriever = ToolsRetriever()
    retriever.add_batch([clock, calculator])

    print(f"Registered Tools: {[get_tool_name(t) for t in retriever.get_all()]}")
    return retriever


@asynccontextmanager
async def setup_tools(tools: List[Tool]) -> AsyncGenerator[List[Tool], None]:
    """Create agent with tools loaded asynchronously."""
    async with AsyncExitStack() as stack:  # noqa
        tools_expanded = []
        for tool in tools:
            if isinstance(tool, ToolsBundle):
                bundle_tools = await stack.enter_async_context(tool.load_async())
                tools_expanded.append(bundle_tools)
            else:
                tools_expanded.append(tool)

        yield tools_expanded


default_retriever = LazyValue(_load_retriever)
default_loader = LazyValue(lambda: ToolsLoader(tools_retriever=default_retriever))
