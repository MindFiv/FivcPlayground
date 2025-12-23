__all__ = [
    "EmbeddingDB",
    "EmbeddingTable",
    "EmbeddingBackend",
    "EmbeddingConfigRepository",
    "create_embedding_db",
]

from fivcplayground.embeddings.types import (
    EmbeddingDB,
    EmbeddingTable,
    EmbeddingBackend,
    EmbeddingConfigRepository,
)


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
    if not embedding_backend:
        if raise_exception:
            raise RuntimeError("No embedding backend specified")

        return None

    if not embedding_config_repository:
        from fivcplayground.embeddings.types.repositories.files import (
            FileEmbeddingConfigRepository,
        )

        embedding_config_repository = FileEmbeddingConfigRepository()

    embedding_config = embedding_config_repository.get_embedding_config(
        embedding_config_id,
    )

    if not embedding_config:
        if raise_exception:
            raise ValueError(f"Embedding not found {embedding_config_id}")
        return None

    return embedding_backend.create_embedding_db(
        embedding_config, space_id=space_id, **kwargs
    )
