from abc import ABC, abstractmethod

from fivcplayground.embeddings.types.base import EmbeddingConfig


class EmbeddingConfigRepository(ABC):
    """
    Abstract base class for embedding configuration data repositories.

    Defines the interface for persisting and retrieving embedding configuration data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @abstractmethod
    async def update_embedding_config_async(
        self, embedding_config: EmbeddingConfig
    ) -> None:
        """Create or update an embedding configuration."""

    @abstractmethod
    async def get_embedding_config_async(
        self, embedding_id: str
    ) -> EmbeddingConfig | None:
        """Retrieve an embedding configuration by ID."""

    @abstractmethod
    async def list_embedding_configs_async(self, **kwargs) -> list[EmbeddingConfig]:
        """List all embedding configurations in the repository."""

    @abstractmethod
    async def delete_embedding_config_async(self, embedding_id: str) -> None:
        """Delete an embedding configuration."""
