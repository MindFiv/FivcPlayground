__all__ = [
    "create_tool_retriever",
    "setup_tools",
    "Tool",
    "ToolBundle",
    "ToolRetriever",
    "ToolLoader",
]

from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator, List

from fivcplayground.embeddings import EmbeddingConfigRepository
from fivcplayground.tools.types import (
    ToolRetriever,
    ToolLoader,
)
from fivcplayground.tools.types.backends import (
    Tool,
    ToolBundle,
)


def create_tool_retriever(
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    load_builtin_tools: bool = True,
    **kwargs,  # ignore additional kwargs
) -> ToolRetriever:
    """Create a new ToolRetriever instance."""
    retriever = ToolRetriever(
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
    )
    if load_builtin_tools:
        from fivcplayground.tools.clock import clock
        from fivcplayground.tools.calculator import calculator

        retriever.add_batch([clock, calculator])

    return retriever


@asynccontextmanager
async def setup_tools(tools: List[Tool]) -> AsyncGenerator[List[Tool], None]:
    """Create agent with tools loaded asynchronously."""
    async with AsyncExitStack() as stack:  # noqa
        tools_expanded = []
        for tool in tools:
            if isinstance(tool, ToolBundle):
                bundle_tools = await stack.enter_async_context(tool.load_async())
                tools_expanded.append(bundle_tools)
            else:
                tools_expanded.append(tool)

        yield tools_expanded
