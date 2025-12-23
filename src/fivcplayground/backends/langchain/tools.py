# import asyncio
import contextlib

from typing import (
    Any,
    AsyncGenerator,
    Callable,
    List,
    Generator,
)

from langchain_core.tools import tool
from langchain_mcp_adapters.sessions import (
    StdioConnection,
    SSEConnection,
    StreamableHttpConnection,
    create_session,
)
from langchain_mcp_adapters.tools import load_mcp_tools

from fivcplayground.tools import (
    ToolConfig,
    Tool,
    ToolBundle,
    ToolBackend,
)


class LangchainTool(Tool):
    """Wrapper for langchain tools"""

    def __init__(self, raw_tool: Any):
        self._tool = raw_tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description

    def get_underlying(self) -> Any:
        return self._tool


class LangchainToolBundle(ToolBundle):
    """Wrapper for langchain tool bundles"""

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

    @contextlib.contextmanager
    def load(self) -> Generator[List[Tool], None]:
        raise NotImplementedError("Not implemented yet.")

    @contextlib.asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        """load tool bundle asynchronously"""
        if self._tool_config.transport == "stdio":
            conn = StdioConnection(
                transport="stdio",
                command=self._tool_config.command,
                args=self._tool_config.args,
                env=self._tool_config.env,
            )
        elif self._tool_config.transport == "sse":
            conn = SSEConnection(
                transport="sse",
                url=self._tool_config.url,
            )
        elif self._tool_config.transport == "streamable_http":
            conn = StreamableHttpConnection(
                transport="streamable_http",
                url=self._tool_config.url,
            )
        else:
            raise ValueError(f"Unsupported transport: {self._tool_config.transport}")

        async with create_session(conn) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            tools = [LangchainTool(t) for t in tools]
            yield tools


class LangchainToolBackend(ToolBackend):
    """Tool backend for langchain"""

    def create_tool(self, tool_func: Callable) -> Tool:
        return LangchainTool(tool(tool_func))

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        return LangchainToolBundle(tool_config)
