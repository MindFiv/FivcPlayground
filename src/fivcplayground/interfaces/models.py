from abc import abstractmethod
from typing import Any, Iterable

from fivcglue.interfaces import IComponent


class IModel(IComponent):
    """Interface for LLM models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the model."""

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
