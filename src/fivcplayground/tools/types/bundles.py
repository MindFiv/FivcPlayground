from collections.abc import Callable
import functools
from typing import Any

from .base import Tool, ToolBackend, ToolBundle, ToolBundleContext


class CallableToolContext(ToolBundleContext):
    """Context manager for callable tool bundles."""

    def __init__(
        self,
        tool_backend: ToolBackend,
        tool_functions: list[Tool],
        tool_classes: list[Callable],
        context: dict[str, Any] | None,
    ):
        self._tool_backend = tool_backend
        self._tool_functions = tool_functions
        self._tool_classes = tool_classes
        self._context = context or {}
        self._class_tools: list[Tool] = []

    async def __aenter__(self) -> list[Tool]:
        """Enter the context and return the list of tools."""
        self._class_tools = []
        for tool_class in self._tool_classes:
            tool_instance = tool_class(**self._context)
            if not callable(tool_instance):
                class_name = getattr(
                    tool_class, "__name__", type(tool_instance).__name__
                )
                raise ValueError(f"Class tool '{class_name}' must implement __call__.")

            tool_name = type(tool_instance).__name__
            tool_description = getattr(tool_instance.__call__, "__doc__", None) or ""

            @functools.wraps(tool_instance.__call__)
            def tool_func(*args, __tool_instance=tool_instance, **kwargs):
                return __tool_instance(*args, **kwargs)

            self._class_tools.append(
                self._tool_backend.create_tool(
                    tool_func,
                    tool_name=tool_name,
                    tool_description=tool_description,
                )
            )
        return [*self._tool_functions, *self._class_tools]

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._class_tools.clear()


class CallableToolBundle(ToolBundle):
    """Tool bundle for function and class based Python callables."""

    def __init__(
        self,
        name: str,
        description: str,
        tool_backend: ToolBackend,
        tool_callables: list[Callable],
    ):
        self._name = name
        self._description = description
        self._tool_backend = tool_backend
        self._tool_functions = [
            tool_backend.create_tool(func)
            for func in tool_callables
            if getattr(func, "kind", "function") == "function"
        ]
        self._tool_classes = [
            func for func in tool_callables if getattr(func, "kind", None) == "class"
        ]
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

    def setup(self, **context: Any) -> ToolBundleContext:
        return CallableToolContext(
            tool_backend=self._tool_backend,
            tool_functions=self._tool_functions,
            tool_classes=self._tool_classes,
            context=context,
        )


FunctionToolBundle = CallableToolBundle
ClassToolBundle = CallableToolBundle
