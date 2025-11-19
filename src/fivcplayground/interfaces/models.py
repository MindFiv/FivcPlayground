from abc import abstractmethod
from typing import Any, Iterable

from pydantic import BaseModel, Field
from fivcglue.interfaces import IComponent


class ModelConfig(BaseModel):
    """Configuration for a model."""

    provider: str = Field(default="openai", description="Model provider")
    model: str = Field(default="gpt-4o-mini", description="Model name")
    api_key: str | None = Field(
        default=None, description="API key for the model provider"
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the model",
    )
    temperature: float = Field(
        default=0.5,
        description="Temperature for the model",
    )


class IModelConfigProvider(IComponent):
    """Interface for model configuration provider."""

    @abstractmethod
    def get_model_config(
        self,
        name: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> ModelConfig | None:
        """Get a model configuration by name."""


class IModel(IComponent):
    """Interface for LLM models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the model."""

    @property
    @abstractmethod
    def config(self) -> ModelConfig:
        """Setting of the model."""

    @abstractmethod
    def get_underlying(self) -> Any:
        """Get the underlying model object."""


class IModelProvider(IComponent):
    """Interface for LLM model creation."""

    @abstractmethod
    def get_model(
        self,
        name: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> IModel | None:
        """get a model instance."""

    @abstractmethod
    def list_models(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> Iterable[IModel]:
        """List all available models."""
