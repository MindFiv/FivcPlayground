from typing import Any, Callable, List

from fastmcp.client.transports import (
    SSETransport,
    StdioTransport,
    StreamableHttpTransport,
)
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.tools import Tool as PydanticAIToolUnderlying

from fivcplayground.tools import (
    CallableToolBundle,
    Tool,
    ToolBackend,
    ToolBundle,
    ToolBundleContext,
    ToolConfig,
)
from fivcplayground.tools.types import ToolConfigTransport
from fivcplayground.utils import DynamicCallable


class PydanticAITool(Tool):
    """Wrapper for a Pydantic AI tool or toolset."""

    def __init__(
        self,
        raw_tool: Any,
        *,
        name: str | None = None,
        description: str | None = None,
    ):
        self._tool = raw_tool
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self._tool.name

    @property
    def description(self) -> str:
        if self._description is not None:
            return self._description
        return self._tool.description or ""

    def get_underlying(self) -> Any:
        return self._tool


class PydanticAIToolBundleContext(ToolBundleContext):
    """Context manager that exposes an MCP server as a Pydantic AI toolset."""

    def __init__(self, tool_config: ToolConfig):
        if tool_config.transport == "stdio":
            transport = StdioTransport(
                command=tool_config.command,
                args=tool_config.args or [],
                env=tool_config.env,
            )
            client: Any = transport
        elif tool_config.transport == "sse":
            client = SSETransport(url=tool_config.url)
        elif tool_config.transport == "streamable_http":
            client = StreamableHttpTransport(url=tool_config.url)
        else:
            raise ValueError(f"Unsupported transport: {tool_config.transport}")

        self._bundle_name = tool_config.id
        self._bundle_description = tool_config.description
        self._toolset = MCPToolset(client)

    async def __aenter__(self) -> List[Tool]:
        """Return the toolset without opening its MCP connection."""
        prefixed_toolset = self._toolset.prefixed(f"mcp__{self._bundle_name}_")
        return [
            PydanticAITool(
                prefixed_toolset,
                name=self._bundle_name,
                description=self._bundle_description,
            )
        ]

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Leave cleanup to the Pydantic AI agent's toolset lifecycle."""
        return None


class PydanticAIToolBundle(ToolBundle):
    """Wrapper for MCP tool bundles."""

    def __init__(self, tool_config: ToolConfig):
        self._tool_config = tool_config

    @property
    def name(self) -> str:
        return self._tool_config.id

    @property
    def description(self) -> str:
        return self._tool_config.description

    def get_underlying(self) -> Any:
        """Return a lightweight callable for indexing and display."""

        def _func() -> str:
            return self.description

        return PydanticAIToolUnderlying(
            _func,
            name=self.name,
            description=self.description,
        )

    def setup(self, **context: Any) -> ToolBundleContext:
        del context
        return PydanticAIToolBundleContext(self._tool_config)


class PydanticAIToolBackend(ToolBackend):
    """Tool backend for Pydantic AI."""

    def create_tool(
        self,
        tool_func: Callable,
        tool_name: str | None = None,
        tool_description: str | None = None,
    ) -> Tool:
        underlying = PydanticAIToolUnderlying(
            tool_func,
            name=tool_name,
            description=tool_description,
        )
        return PydanticAITool(underlying)

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        if tool_config.transport == ToolConfigTransport.FUNCTION:
            if not tool_config.functions:
                raise ValueError(
                    f"ToolConfig '{tool_config.id}' has transport 'function' "
                    "but 'functions' is None or empty."
                )
            funcs = [DynamicCallable(path) for path in tool_config.functions]
            return CallableToolBundle(
                name=tool_config.id,
                description=tool_config.description,
                tool_backend=self,
                tool_callables=funcs,
            )
        return PydanticAIToolBundle(tool_config)
