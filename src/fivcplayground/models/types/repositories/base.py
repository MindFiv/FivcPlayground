from abc import ABC, abstractmethod
from typing import List

from fivcplayground.models.types.base import ModelConfig


class ModelConfigRepository(ABC):
    """
    Abstract base class for model data repositories.

    Defines the interface for persisting and retrieving model data.
    Implementations can use different storage backends (files, databases, etc.).
    """

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
