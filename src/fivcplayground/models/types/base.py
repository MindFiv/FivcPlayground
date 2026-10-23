from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ModelConfig(BaseModel):
    """
    Model configuration.

    This class represents the configuration for a model, including its name,
    description, and any additional parameters.
    """

    id: str = Field(..., description="Unique identifier for the model")
    # name: str = Field(..., description="Name of the model")
    description: str | None = Field(
        default=None, description="Description of the model"
    )
    provider: str = Field(..., description="Provider of the model")
    model: str = Field(..., description="Model name (e.g., 'gpt-4', 'llama2')")
    api_key: str | None = Field(
        default=None, description="API key for the model (if required)"
    )
    base_url: str | None = Field(
        default=None, description="Base URL for the model (if applicable)"
    )
    temperature: float | None = Field(
        default=None, description="Temperature for the model (if applicable)"
    )
    max_tokens: int | None = Field(
        default=None, description="Maximum tokens for the model (if applicable)"
    )
    enable_thinking: bool | None = Field(
        default=None,
        description="Enable provider-supported thinking output when explicitly set.",
    )

    extra: dict[str, Any] | None = Field(
        default=None,
        description="Backend-specific, serializable model service configuration.",
    )

    @model_validator(mode="after")
    def validate_extra_does_not_override_canonical_fields(self):
        extra = self.extra or {}
        canonical = set(type(self).model_fields)
        conflicts = sorted(canonical.intersection(extra))
        if conflicts:
            raise ValueError(
                "extra must not override canonical ModelConfig fields: "
                + ", ".join(conflicts)
            )
        return self


class Model(ABC):
    """Abstract base class for models."""

    # @property
    # @abstractmethod
    # def id(self) -> str:
    #     """Get the id of the model."""

    @abstractmethod
    def get_underlying(self) -> Any:
        """Get the underlying model instance."""


class ModelBackend(ABC):
    """Interface for model backends."""

    @abstractmethod
    def create_model(self, model_config: ModelConfig) -> Model:
        """Create a model instance from a ModelConfig."""
