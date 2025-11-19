from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncGenerator,
    Iterable,
    List,
    Optional,
)

from fivcglue.interfaces import IComponent


class ITool(IComponent):
    """Interface for individual tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the tool."""

    @abstractmethod
    def get_underlying(self) -> Any:
        """Get the underlying tool object."""


class IToolBundle(ITool):
    """Interface for tool bundles."""

    @asynccontextmanager
    @abstractmethod
    async def setup_async(self) -> AsyncGenerator[List[ITool], None]:
        """Get the tools in the bundle."""

    def get_underlying(self) -> Any:
        """Get the underlying tool bundle object."""
        raise NotImplementedError("IToolBundle.get_underlying not implemented")


class IToolProvider(IComponent):
    """Interface for tools storage and retrieval."""

    @abstractmethod
    def list_tools(
        self,
        user_id: str | None = None,
        names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """List all tools."""

    @abstractmethod
    def get_tool(
        self,
        name: str,
        **kwargs: Any,
    ) -> ITool | None:
        """Get a tool by name."""

    @abstractmethod
    def search_tools(
        self,
        query: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """Search for tools."""
