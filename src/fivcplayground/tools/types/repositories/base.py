from abc import ABC, abstractmethod
from typing import List
from typing_extensions import deprecated

from fivcplayground.tools.types.base import ToolConfig


class ToolConfigRepository(ABC):
    """
    Abstract base class for tool data repositories.

    Defines the interface for persisting and retrieving tool data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @deprecated("Use update_tool_config_async instead")
    def update_tool_config(self, tool_config: ToolConfig) -> None:
        """Create or update a tool configuration."""

    @deprecated("Use get_tool_config_async instead")
    def get_tool_config(self, tool_id: str) -> ToolConfig | None:
        """Retrieve a tool by ID."""

    @deprecated("Use list_tool_configs_async instead")
    def list_tool_configs(self, **kwargs) -> List[ToolConfig]:
        """List all tools in the repository."""

    @deprecated("Use delete_tool_config_async instead")
    def delete_tool_config(self, tool_id: str) -> None:
        """Delete a tool configuration."""

    @abstractmethod
    async def update_tool_config_async(self, tool_config: ToolConfig) -> None:
        """Create or update a tool configuration."""

    @abstractmethod
    async def get_tool_config_async(self, tool_id: str) -> ToolConfig | None:
        """Retrieve a tool by ID."""

    @abstractmethod
    async def list_tool_configs_async(self, **kwargs) -> List[ToolConfig]:
        """List all tools in the repository."""

    @abstractmethod
    async def delete_tool_config_async(self, tool_id: str) -> None:
        """Delete a tool configuration."""
