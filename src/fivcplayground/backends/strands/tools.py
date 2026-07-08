from typing import (
    Any,
    Callable,
    List,
)

from mcp import StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from strands.tools import tool
from strands.tools.mcp import MCPClient
from strands.types.tools import AgentTool as StrandToolUnderling

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


class StrandsTool(Tool):
    """Wrapper for strands tools"""

    def __init__(self, raw_tool: StrandToolUnderling):
        self._tool = raw_tool

    @property
    def name(self) -> str:
        return self._tool.tool_name

    @property
    def description(self) -> str:
        return self._tool.tool_spec.get("description") or ""

    def get_underlying(self) -> Any:
        return self._tool


class StrandsToolBundleContext(ToolBundleContext):
    """Context manager for strands tool bundles"""

    def __init__(self, tool_config: ToolConfig):
        if tool_config.transport == "stdio":
            c = stdio_client(
                StdioServerParameters(
                    command=tool_config.command,
                    args=tool_config.args,
                    env=tool_config.env,
                )
            )
        elif tool_config.transport == "sse":
            c = sse_client(url=tool_config.url)
        elif tool_config.transport == "streamable_http":
            c = streamable_http_client(url=tool_config.url)
        else:
            raise ValueError(f"Unsupported transport: {tool_config.transport}")

        self._bundle_name = tool_config.id
        self._client = MCPClient(lambda: c)

    async def __aenter__(self) -> List[Tool]:
        """Enter the context and return the list of tools."""
        c = self._client.__enter__()
        tools = c.list_tools_sync(prefix=f"mcp__{self._bundle_name}__")
        return list(StrandsTool(t) for t in tools)

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the context."""
        self._client.__exit__(exc_type, exc_value, traceback)


class StrandsToolBundle(ToolBundle):
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

        return tool(name=self.name, description=self.description)(_func)

    def setup(self, **context: Any) -> ToolBundleContext:
        return StrandsToolBundleContext(self._tool_config)


class StrandsToolBackend(ToolBackend):
    """Tool backend for strands"""

    def create_tool(
        self,
        tool_func: Callable,
        tool_name: str | None = None,
        tool_description: str | None = None,
    ) -> Tool:
        if tool_name and tool_description:
            tool_underlying = tool(name=tool_name, description=tool_description)(
                tool_func
            )
        else:
            tool_underlying = tool(tool_func)
        return StrandsTool(tool_underlying)

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        if tool_config.transport == ToolConfigTransport.FUNCTION:
            if not tool_config.functions:
                raise ValueError(
                    f"ToolConfig '{tool_config.id}' has transport 'function' "
                    "but 'functions' is None or empty."
                )
            funcs = [DynamicCallable(p) for p in tool_config.functions]
            return CallableToolBundle(
                name=tool_config.id,
                description=tool_config.description,
                tool_backend=self,
                tool_callables=funcs,
            )
        return StrandsToolBundle(tool_config)
