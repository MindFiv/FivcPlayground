from collections.abc import Callable
from typing import Any

from .base import Tool, ToolBackend, ToolBundle, ToolBundleContext


class FunctionToolContext(ToolBundleContext):
    """Context manager for function tool bundles"""

    def __init__(self, tools: list[Tool]):
        self._tools = tools

    async def __aenter__(self) -> list[Tool]:
        """Enter the context and return the list of tools."""
        return self._tools

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the context."""
        pass


class FunctionToolBundle(ToolBundle):
    """Tool bundle for function tools"""

    def __init__(
        self,
        name: str,
        description: str,
        tool_backend: ToolBackend,
        tool_funcs: list[Callable],
    ):
        self._name = name
        self._description = description
        self._tools = [tool_backend.create_tool(func) for func in tool_funcs]
        self._underlying_tool = tool_backend.create_tool(
            lambda: description,
            tool_name=name,
            tool_description=description,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_underlying(self) -> Any:
        return self._underlying_tool.get_underlying()

    def setup(self) -> ToolBundleContext:
        return FunctionToolContext(self._tools)
