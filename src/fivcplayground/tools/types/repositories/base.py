from abc import ABC, abstractmethod
from typing import List

from fivcplayground.tools.types.base import ToolConfig


class ToolConfigRepository(ABC):
    """
    Abstract base class for tool data repositories.

    Defines the interface for persisting and retrieving tool data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @abstractmethod
    def update_tool_config(self, tool_config: ToolConfig) -> None:
        """Create or update a tool configuration."""

    @abstractmethod
    def get_tool_config(self, tool_id: str) -> ToolConfig | None:
        """Retrieve a tool by ID."""

    @abstractmethod
    def list_tool_configs(self, **kwargs) -> List[ToolConfig]:
        """List all tools in the repository."""

    @abstractmethod
    def delete_tool_config(self, tool_id: str) -> None:
        """Delete a tool configuration."""
