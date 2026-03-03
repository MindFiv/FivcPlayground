__all__ = [
    "create_builtin_tools_async",
    "create_tool_retriever_async",
    "Tool",
    "ToolBundle",
    "ToolBundleContext",
    "ToolBackend",
    "ToolConfig",
    "ToolConfigRepository",
    "ToolRetriever",
]

from fivcplayground.embeddings import (
    EmbeddingBackend,
    EmbeddingConfigRepository,
    create_embedding_db_async,
)

from .types import (
    FunctionToolBundle,
    Tool,
    ToolBackend,
    ToolBundle,
    ToolBundleContext,
    ToolConfig,
    ToolRetriever,
)
from .types.repositories.base import (
    ToolConfigRepository,
)


async def create_builtin_tools_async(
    tool_backend: ToolBackend | None = None,
    raise_exception: bool = True,
) -> list[Tool]:
    """Async version of create_tools."""
    if tool_backend is None:
        if raise_exception:
            raise RuntimeError("tool_backend is required")

        return []

    from fivcplayground.tools.calculator import calculator
    from fivcplayground.tools.clock import clock
    from fivcplayground.tools.filesystem import (
        file_read,
        file_search,
        file_write,
    )
    from fivcplayground.tools.shell import shell

    return [
        FunctionToolBundle(
            name="auxiliary",
            description="Auxiliary tools like clock and calculator",
            tool_backend=tool_backend,
            tool_funcs=[clock, calculator],
        ),
        FunctionToolBundle(
            name="filesystem",
            description="Tools for interacting with the filesystem",
            tool_backend=tool_backend,
            tool_funcs=[
                file_read,
                file_write,
                file_search,
            ],
        ),
        tool_backend.create_tool(shell),
    ]


async def create_tool_retriever_async(
    tool_backend: ToolBackend | None = None,
    tools: list[Tool] | None = None,  # for builtin tools
    tool_config_repository: ToolConfigRepository | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> ToolRetriever | None:
    """Async version of create_tool_retriever."""
    if tool_backend is None:
        if raise_exception:
            raise RuntimeError(
                "tool_backend is required. Please provide a ToolBackend instance "
                "(e.g., StrandsToolBackend() or LangchainToolBackend())"
            )
        return None

    if not embedding_config_repository:
        if raise_exception:
            raise RuntimeError("No embedding config repository specified")

        return None

    if not tool_config_repository:
        if raise_exception:
            raise RuntimeError("No tool config repository specified")

        return None

    embedding_db = await create_embedding_db_async(
        embedding_backend=embedding_backend,
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
        space_id=space_id,
        raise_exception=raise_exception,
    )
    if not embedding_db:
        if raise_exception:
            raise RuntimeError(f"Embedding not found {embedding_config_id}")
        return None

    tools = tools or []

    return ToolRetriever(
        tool_backend=tool_backend,
        tools=tools,
        tool_config_repository=tool_config_repository,
        embedding_db=embedding_db,
    )
