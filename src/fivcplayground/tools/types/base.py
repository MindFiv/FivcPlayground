from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
)

from pydantic import BaseModel, Field


class ToolConfigTransport(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


class ToolConfig(BaseModel):
    """Configuration for a tool."""

    id: str = Field(..., description="Unique identifier for the tool")
    # name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")
    transport: ToolConfigTransport = Field(
        ...,
        description="Transport protocol for the tool",
    )
    command: str | None = Field(None, description="Command to run the tool")
    args: List[str] | None = Field(None, description="Arguments for the command")
    env: Dict[str, str] | None = Field(None, description="Environment variables")
    url: str | None = Field(None, description="URL for the tool")


class Tool(ABC):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the tool."""

    @abstractmethod
    def get_underlying(self) -> Any:
        """Get the underlying tool instance."""


class ToolBundleContext(ABC):
    """Context manager for tool bundles."""

    @abstractmethod
    async def __aenter__(self) -> List[Tool]:
        """Enter the context and return the list of tools."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the context."""


class ToolBundle(Tool):
    """Tool bundle that groups multiple tools from the same MCP server."""

    @abstractmethod
    def setup(self) -> ToolBundleContext:
        """set up the tool bundle."""

    # @abstractmethod
    # def load(self) -> Generator[List[Tool], None]:
    #     """Load the tools in the bundle synchronously."""
    #
    # @abstractmethod
    # async def load_async(self) -> AsyncGenerator[List[Tool], None]:
    #     """Load the tools in the bundle asynchronously."""


class ToolBackend(ABC):
    """Interface for tool backends."""

    @abstractmethod
    def create_tool(self, tool_func: Callable) -> Tool:
        """Create a tool instance from a ToolConfig."""

    @abstractmethod
    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        """Create a tool bundle from a ToolConfig."""
