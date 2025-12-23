__all__ = [
    "create_tool_retriever",
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
    create_embedding_db,
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
    if tool_backend is None:
        if raise_exception:
            raise RuntimeError(
                "tool_backend is required. Please provide a ToolBackend instance "
                "(e.g., StrandsToolBackend() or LangchainToolBackend())"
            )
        return None

    if not embedding_config_repository:
        from fivcplayground.embeddings.types.repositories.files import (
            FileEmbeddingConfigRepository,
        )

        embedding_config_repository = FileEmbeddingConfigRepository()

    if not tool_config_repository:
        from fivcplayground.tools.types.repositories.files import (
            FileToolConfigRepository,
        )

        tool_config_repository = FileToolConfigRepository()

    embedding_db = create_embedding_db(
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
