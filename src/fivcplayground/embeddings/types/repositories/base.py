from asyncio import run as asyncio_run
from abc import ABC, abstractmethod
from typing_extensions import deprecated

from fivcplayground.embeddings.types.base import EmbeddingConfig


class EmbeddingConfigRepository(ABC):
    """
    Abstract base class for embedding configuration data repositories.

    Defines the interface for persisting and retrieving embedding configuration data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @deprecated("Use update_embedding_config_async instead")
    def update_embedding_config(self, embedding_config: EmbeddingConfig) -> None:
        """Create or update an embedding configuration."""
        return asyncio_run(self.update_embedding_config_async(embedding_config))

    @deprecated("Use get_embedding_config_async instead")
    def get_embedding_config(self, embedding_id: str) -> EmbeddingConfig | None:
        """Retrieve an embedding configuration by ID."""
        return asyncio_run(self.get_embedding_config_async(embedding_id))

    @deprecated("Use list_embedding_configs_async instead")
    def list_embedding_configs(self, **kwargs) -> list[EmbeddingConfig]:
        """List all embedding configurations in the repository."""
        return asyncio_run(self.list_embedding_configs_async(**kwargs))

    @deprecated("Use delete_embedding_config_async instead")
    def delete_embedding_config(self, embedding_id: str) -> None:
        """Delete an embedding configuration."""
        return asyncio_run(self.delete_embedding_config_async(embedding_id))

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
