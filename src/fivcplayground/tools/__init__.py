__all__ = [
    "create_tool_retriever",
    "create_tool_loader",
    "setup_tools",
    "Tool",
    "ToolBundle",
    "ToolRetriever",
    "ToolLoader",
    "ToolConfig",
    "ToolConfigRepository",
]

from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator, List

from fivcplayground.embeddings import EmbeddingConfigRepository
from fivcplayground.tools.types import (
    ToolRetriever,
    ToolLoader,
    Tool,
    ToolConfig,
    ToolBundle,
)
from fivcplayground.tools.types.repositories import ToolConfigRepository


def create_tool_retriever(
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    load_builtin_tools: bool = True,
    **kwargs,  # ignore additional kwargs
) -> ToolRetriever:
    """
    Create a new ToolRetriever instance.

    Args:
        embedding_config_repository: Repository for embedding configurations
        embedding_config_id: ID of the embedding configuration to use
        space_id: Optional embedding space identifier for data isolation.
                 If None, uses "default" (shared space).
                 Examples: "user_alice", "project_website", "env_staging"
        load_builtin_tools: Whether to load built-in tools (clock, calculator)
        **kwargs: Additional arguments

    Returns:
        ToolRetriever instance configured for the specified embedding space

    Examples:
        # Default/shared space (backward compatible)
        retriever = create_tool_retriever()

        # User-specific space
        retriever = create_tool_retriever(space_id="user_alice")

        # Project-specific space with custom config
        retriever = create_tool_retriever(
            embedding_config_id="openai-ada",
            space_id="project_website"
        )

        # Environment-specific space without builtin tools
        retriever = create_tool_retriever(
            space_id="env_production",
            load_builtin_tools=False
        )
    """
    retriever = ToolRetriever(
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
        space_id=space_id,
    )
    retriever.add_tool(retriever.to_tool())  # Add self to retriever

    if load_builtin_tools:
        from fivcplayground.tools.clock import clock
        from fivcplayground.tools.calculator import calculator

        retriever.add_tool(clock)
        retriever.add_tool(calculator)

    return retriever


def create_tool_loader(
    tool_retriever: ToolRetriever | None = None,
    tool_config_repository: ToolConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> ToolLoader:
    """Create a new ToolLoader instance."""
    if not tool_retriever:
        raise ValueError("tool_retriever must be provided")

    return ToolLoader(
        tool_retriever=tool_retriever,
        tool_config_repository=tool_config_repository,
        **kwargs,
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
