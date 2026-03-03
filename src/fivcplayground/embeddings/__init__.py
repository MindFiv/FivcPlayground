__all__ = [
    "EmbeddingDB",
    "EmbeddingTable",
    "EmbeddingBackend",
    "EmbeddingConfigRepository",
    "create_embedding_db_async",
]

from fivcplayground.embeddings.types import (
    EmbeddingDB,
    EmbeddingTable,
    EmbeddingBackend,
    EmbeddingConfigRepository,
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
