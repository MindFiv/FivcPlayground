__all__ = [
    "create_tool_retriever",
    "create_tool_retriever_async",
    "Tool",
    "ToolBundle",
    "ToolBundleContext",
    "ToolBackend",
    "ToolConfig",
    "ToolConfigRepository",
    "ToolRetriever",
]

from typing_extensions import deprecated

from fivcplayground.embeddings import (
    EmbeddingBackend,
    EmbeddingConfigRepository,
    create_embedding_db_async,
)
from fivcplayground.tools.types import (
    ToolRetriever,
    ToolConfig,
    Tool,
    ToolBundle,
    ToolBundleContext,
    ToolBackend,
)
from fivcplayground.tools.types.repositories.base import (
    ToolConfigRepository,
)


@deprecated("Use create_tool_retriever_async instead")
def create_tool_retriever(
    tool_backend: ToolBackend | None = None,
    tool_config_repository: ToolConfigRepository | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    load_builtin_tools: bool = True,
    **kwargs,  # ignore additional kwargs
) -> ToolRetriever | None:
    """Create a tool retriever.

    Args:
        tool_backend: The tool backend to use (required). Must be an instance of ToolBackend
                     (e.g., StrandsToolBackend or LangchainToolBackend).
        tool_config_repository: Repository for tool configurations. If None, uses FileToolConfigRepository.
        embedding_backend: The embedding backend to use (required). Must be an instance of EmbeddingBackend
        embedding_config_repository: Repository for embedding configurations. If None, uses FileEmbeddingConfigRepository.
        embedding_config_id: ID of the embedding configuration to use. Defaults to "default".
        space_id: Optional space ID for multi-tenancy support.
        raise_exception: Whether to raise exception if config not found. Defaults to True.
        load_builtin_tools: Whether to load built-in tools (clock, calculator). Defaults to True.
        **kwargs: Additional keyword arguments (ignored).

    Returns:
        ToolRetriever: A configured tool retriever instance.

    Raises:
        TypeError: If tool_backend is not provided or is not a ToolBackend instance.
    """
    import asyncio

    return asyncio.run(
        create_tool_retriever_async(
            tool_backend=tool_backend,
            tool_config_repository=tool_config_repository,
            embedding_backend=embedding_backend,
            embedding_config_repository=embedding_config_repository,
            embedding_config_id=embedding_config_id,
            space_id=space_id,
            raise_exception=raise_exception,
            load_builtin_tools=load_builtin_tools,
            **kwargs,
        )
    )


async def create_tool_retriever_async(
    tool_backend: ToolBackend | None = None,
    tool_config_repository: ToolConfigRepository | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    load_builtin_tools: bool = True,
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

    tool_list = []
    if load_builtin_tools:
        from fivcplayground.tools.clock import clock
        from fivcplayground.tools.calculator import calculator

        tool_list.append(tool_backend.create_tool(clock))
        tool_list.append(tool_backend.create_tool(calculator))

    return ToolRetriever(
        tool_backend=tool_backend,
        tool_list=tool_list,
        tool_config_repository=tool_config_repository,
        embedding_db=embedding_db,
    )
