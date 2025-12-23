from contextlib import (
    asynccontextmanager,
    contextmanager,
)
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    List,
    Generator,
)

from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from strands.tools import tool
from strands.tools.mcp import MCPClient

from fivcplayground.tools import (
    ToolConfig,
    Tool,
    ToolBundle,
    ToolBackend,
)


class StrandsTool(Tool):
    """Wrapper for strands tools"""

    def __init__(self, raw_tool: Any):
        self._tool = raw_tool

    @property
    def name(self) -> str:
        return self._tool.tool_name

    @property
    def description(self) -> str:
        return self._tool.tool_spec.get("description") or ""

    def get_underlying(self) -> Any:
        return self._tool


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

        return tool(_func)

    @contextmanager
    def load(self) -> Generator[List[Tool], None]:
        if self._tool_config.transport == "stdio":
            c = stdio_client(
                StdioServerParameters(
                    command=self._tool_config.command,
                    args=self._tool_config.args,
                    env=self._tool_config.env,
                )
            )
        elif self._tool_config.transport == "sse":
            c = sse_client(url=self._tool_config.url)
        elif self._tool_config.transport == "streamable_http":
            c = streamablehttp_client(url=self._tool_config.url)
        else:
            raise ValueError(f"Unsupported transport: {self._tool_config.transport}")

        with MCPClient(lambda: c) as client:
            tools = client.list_tools_sync()
            yield list(StrandsTool(tool(t)) for t in tools)

    @asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        if self._tool_config.transport == "stdio":
            c = stdio_client(
                StdioServerParameters(
                    command=self._tool_config.command,
                    args=self._tool_config.args,
                    env=self._tool_config.env,
                )
            )
        elif self._tool_config.transport == "sse":
            c = sse_client(url=self._tool_config.url)
        elif self._tool_config.transport == "streamable_http":
            c = streamablehttp_client(url=self._tool_config.url)
        else:
            raise ValueError(f"Unsupported transport: {self._tool_config.transport}")

        with MCPClient(lambda: c) as client:
            tools = client.list_tools_sync()
            yield list(StrandsTool(t) for t in tools)


class StrandsToolBackend(ToolBackend):
    """Tool backend for strands"""

    def create_tool(self, tool_func: Callable) -> Tool:
        return StrandsTool(tool(tool_func))

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        return StrandsToolBundle(tool_config)
