from abc import ABC, abstractmethod

from fivcplayground.embeddings.types.base import EmbeddingConfig


class EmbeddingConfigRepository(ABC):
    """
    Abstract base class for embedding configuration data repositories.

    Defines the interface for persisting and retrieving embedding configuration data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @abstractmethod
    def update_embedding_config(self, embedding_config: EmbeddingConfig) -> None:
        """Create or update an embedding configuration."""
        ...

    @abstractmethod
    def get_embedding_config(self, embedding_id: str) -> EmbeddingConfig | None:
        """Retrieve an embedding configuration by ID."""
        ...

    @abstractmethod
    def list_embedding_configs(self, **kwargs) -> list[EmbeddingConfig]:
        """List all embedding configurations in the repository."""
        ...

    @abstractmethod
    def delete_embedding_config(self, embedding_id: str) -> None:
        """Delete an embedding configuration."""
        ...
