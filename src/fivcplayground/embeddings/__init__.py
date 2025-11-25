__all__ = [
    "EmbeddingDB",
    "EmbeddingTable",
    "EmbeddingConfigRepository",
    "create_embedding_db",
]

from fivcplayground.embeddings.types import (
    EmbeddingDB,
    EmbeddingTable,
    EmbeddingConfigRepository,
)


def create_embedding_db(
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,
) -> EmbeddingDB | None:
    """Factory function to create an embedding database."""
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

    return EmbeddingDB(embedding_config, **kwargs)
