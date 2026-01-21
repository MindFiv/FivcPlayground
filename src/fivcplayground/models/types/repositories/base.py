from asyncio import run as asyncio_run
from abc import ABC, abstractmethod
from typing import List
from typing_extensions import deprecated

from fivcplayground.models.types.base import ModelConfig


class ModelConfigRepository(ABC):
    """
    Abstract base class for model data repositories.

    Defines the interface for persisting and retrieving model data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @deprecated("Use update_model_config_async instead")
    def update_model_config(self, model_config: ModelConfig) -> None:
        """Create or update a model configuration."""
        return asyncio_run(self.update_model_config_async(model_config))

    @deprecated("Use get_model_config_async instead")
    def get_model_config(self, model_id: str) -> ModelConfig | None:
        """Retrieve a model configuration by ID."""
        return asyncio_run(self.get_model_config_async(model_id))

    @deprecated("Use list_model_configs_async instead")
    def list_model_configs(self, **kwargs) -> List[ModelConfig]:
        """List all model configurations in the repository."""
        return asyncio_run(self.list_model_configs_async(**kwargs))

    @deprecated("Use delete_model_config_async instead")
    def delete_model_config(self, model_id: str) -> None:
        """Delete a model configuration."""
        return asyncio_run(self.delete_model_config_async(model_id))

    @abstractmethod
    async def update_model_config_async(self, model_config: ModelConfig) -> None:
        """Create or update a model configuration."""

    @abstractmethod
    async def get_model_config_async(self, model_id: str) -> ModelConfig | None:
        """Retrieve a model configuration by ID."""

    @abstractmethod
    async def list_model_configs_async(self, **kwargs) -> List[ModelConfig]:
        """List all model configurations in the repository."""

    @abstractmethod
    async def delete_model_config_async(self, model_id: str) -> None:
        """Delete a model configuration."""
