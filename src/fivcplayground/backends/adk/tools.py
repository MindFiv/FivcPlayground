from typing import (
    Any,
    Callable,
    List,
)

from google.adk.tools import FunctionTool, BaseTool as AdkToolUnderlying
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StdioServerParameters,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)

from fivcplayground.tools import (
    FunctionToolBundle,
    Tool,
    ToolBackend,
    ToolBundle,
    ToolBundleContext,
    ToolConfig,
)
from fivcplayground.tools.types import ToolConfigTransport
from fivcplayground.utils import DynamicFunc


class AdkTool(Tool):
    """Wrapper for strands tools"""

    def __init__(self, raw_tool: AdkToolUnderlying):
        self._tool = raw_tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description

    def get_underlying(self) -> Any:
        return self._tool


class AdkToolBundleContext(ToolBundleContext):
    """Context manager for strands tool bundles"""

    def __init__(self, tool_config: ToolConfig):
        if tool_config.transport == "stdio":
            params = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=tool_config.command,
                    args=tool_config.args,
                    env=tool_config.env,
                )
            )
        elif tool_config.transport == "sse":
            params = SseConnectionParams(url=tool_config.url)
        elif tool_config.transport == "streamable_http":
            params = StreamableHTTPConnectionParams(url=tool_config.url)
        else:
            raise ValueError(f"Unsupported transport: {tool_config.transport}")

        self._bundle_name = tool_config.id
        self._client = McpToolset(
            connection_params=params, tool_name_prefix=f"mcp__{self._bundle_name}__"
        )

    async def __aenter__(self) -> List[Tool]:
        """Enter the context and return the list of tools."""
        tools = await self._client.get_tools_with_prefix()
        return list(AdkTool(t) for t in tools)

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._client.close()


class AdkToolBundle(ToolBundle):
    """Wrapper for strands tool bundles"""

    def __init__(self, tool_config: ToolConfig):
        self._tool_config = tool_config

    @property
    def name(self) -> str:
        return self._tool_config.id

    @property
    def description(self) -> str:
        return self._tool_config.description

    def get_underlying(self) -> Any:
        """get underlying tool bundle"""

        def _func(*args: Any, **kwargs: Any) -> str:
            """get description of tool bundle"""
            return self.description

        _func.__name__ = self.name
        _func.__doc__ = self.description

        return FunctionTool(_func)

    def setup(self) -> ToolBundleContext:
        return AdkToolBundleContext(self._tool_config)


class AdkToolBackend(ToolBackend):
    """Tool backend for strands"""

    def create_tool(
        self,
        tool_func: Callable,
        tool_name: str | None = None,
        tool_description: str | None = None,
    ) -> Tool:
        if tool_name and tool_description:
            tool_func.__name__ = tool_name
            tool_func.__doc__ = tool_description

        tool_underlying = FunctionTool(tool_func)
        return AdkTool(tool_underlying)

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        if tool_config.transport == ToolConfigTransport.FUNCTION:
            if not tool_config.functions:
                raise ValueError(
                    f"ToolConfig '{tool_config.id}' has transport 'function' "
                    "but 'functions' is None or empty."
                )
            funcs = [DynamicFunc(p) for p in tool_config.functions]
            return FunctionToolBundle(
                name=tool_config.id,
                description=tool_config.description,
                tool_backend=self,
                tool_funcs=funcs,
            )
        return AdkToolBundle(tool_config)
