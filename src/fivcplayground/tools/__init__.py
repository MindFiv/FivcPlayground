__all__ = [
    "create_tool_retriever",
    "setup_tools",
    "Tool",
    "ToolBundle",
    "ToolRetriever",
    "ToolConfig",
    "ToolConfigRepository",
]

from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator, List

from fivcplayground.embeddings import (
    EmbeddingConfigRepository,
    create_embedding_db,
)
from fivcplayground.tools.types import (
    ToolRetriever,
    Tool,
    ToolConfig,
    ToolBundle,
)
from fivcplayground.tools.types.repositories.base import (
    ToolConfigRepository,
)


def create_tool_retriever(
    tool_config_repository: ToolConfigRepository | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    load_builtin_tools: bool = True,
    **kwargs,  # ignore additional kwargs
) -> ToolRetriever:
    """Create a new ToolRetriever instance.

    Args:
        tool_config_repository: Repository for tool configurations
        embedding_config_repository: Repository for embedding configurations
        embedding_config_id: ID of the embedding configuration to use
        space_id: ID of the embedding space
        load_builtin_tools: Whether to load built-in tools (clock, calculator)
        **kwargs: Additional arguments (ignored)

    Returns:
        ToolRetriever instance with tools loaded
    """
    if not embedding_config_repository:
        from fivcplayground.embeddings.types.repositories.files import (
            FileEmbeddingConfigRepository,
        )

        embedding_config_repository = FileEmbeddingConfigRepository()

    embedding_db = create_embedding_db(
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
        space_id=space_id,
    )

    tool_list = []
    if load_builtin_tools:
        from fivcplayground.tools.clock import clock
        from fivcplayground.tools.calculator import calculator

        tool_list.append(clock)
        tool_list.append(calculator)

    return ToolRetriever(
        tool_list=tool_list,
        tool_config_repository=tool_config_repository,
        embedding_db=embedding_db,
    )


@asynccontextmanager
async def setup_tools(tools: List[Tool]) -> AsyncGenerator[List[Tool], None]:
    """Create agent with tools loaded asynchronously."""
    async with AsyncExitStack() as stack:  # noqa
        tools_expanded = []
        for tool in tools:
            if isinstance(tool, ToolBundle):
                bundle_tools = await stack.enter_async_context(tool.load_async())
                tools_expanded.extend(bundle_tools)
            else:
                tools_expanded.append(tool)

        yield tools_expanded
