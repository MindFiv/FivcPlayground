__all__ = [
    "EmbeddingDB",
    "EmbeddingTable",
    "EmbeddingBackend",
    "EmbeddingConfigRepository",
    "create_embedding_db",
    "create_embedding_db_async",
]

from typing_extensions import deprecated

from fivcplayground.embeddings.types import (
    EmbeddingDB,
    EmbeddingTable,
    EmbeddingBackend,
    EmbeddingConfigRepository,
)


@deprecated("Use create_embedding_db_async instead")
def create_embedding_db(
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    **kwargs,
) -> EmbeddingDB | None:
    """
    Factory function to create an embedding database.

    Args:
        embedding_backend: The embedding backend to use (required). Must be an instance of EmbeddingBackend
        embedding_config_repository: Repository for embedding configurations
        embedding_config_id: ID of the embedding configuration to use
        space_id: Optional embedding space identifier for data isolation.
                 If None, uses "default" (shared space).
                 Examples: "user_alice", "project_website", "env_staging"
        raise_exception: Whether to raise exception if config not found
        **kwargs: Additional arguments passed to EmbeddingDB

    Returns:
        EmbeddingDB instance or None if config not found and raise_exception=False

    Examples:
        # Default/shared space (backward compatible)
        db = create_embedding_db()

        # User-specific space
        db = create_embedding_db(space_id="user_alice")

        # Project-specific space
        db = create_embedding_db(space_id="project_website")
    """
    import asyncio

    return asyncio.run(
        create_embedding_db_async(
            embedding_backend=embedding_backend,
            embedding_config_repository=embedding_config_repository,
            embedding_config_id=embedding_config_id,
            space_id=space_id,
            raise_exception=raise_exception,
            **kwargs,
        )
    )


async def create_embedding_db_async(
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    **kwargs,
) -> EmbeddingDB | None:
    """Async version of create_embedding_db."""
    if not embedding_backend:
        if raise_exception:
            raise RuntimeError("No embedding backend specified")

        return None

    if not embedding_config_repository:
        if raise_exception:
            raise RuntimeError("No embedding config repository specified")

        return None

    embedding_config = await embedding_config_repository.get_embedding_config_async(
        embedding_config_id,
    )

    if not embedding_config:
        if raise_exception:
            raise ValueError(f"Embedding not found {embedding_config_id}")
        return None

    return embedding_backend.create_embedding_db(
        embedding_config, space_id=space_id, **kwargs
    )
