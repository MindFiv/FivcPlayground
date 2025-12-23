from typing import (
    Any,
    Callable,
    List,
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
    ToolBundleContext,
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


class LangchainToolContext(ToolBundleContext):
    """Context manager for strands tool bundles"""

    def __init__(self, tool_config: ToolConfig):
        if tool_config.transport == "stdio":
            conn = StdioConnection(
                transport="stdio",
                command=tool_config.command,
                args=tool_config.args,
                env=tool_config.env,
            )
        elif tool_config.transport == "sse":
            conn = SSEConnection(
                transport="sse",
                url=tool_config.url,
            )
        elif tool_config.transport == "streamable_http":
            conn = StreamableHttpConnection(
                transport="streamable_http",
                url=tool_config.url,
            )
        else:
            raise ValueError(f"Unsupported transport: {tool_config.transport}")

        self._session = create_session(conn)

    async def __aenter__(self) -> List[Tool]:
        """Enter the context and return the list of tools."""
        s = await self._session.__aenter__()
        await s.initialize()
        tools = await load_mcp_tools(s)
        return list(LangchainTool(t) for t in tools)

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the context."""
        await self._session.__aexit__(exc_type, exc_value, traceback)


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

    def setup(self) -> ToolBundleContext:
        return LangchainToolContext(self._tool_config)


class LangchainToolBackend(ToolBackend):
    """Tool backend for langchain"""

    def create_tool(self, tool_func: Callable) -> Tool:
        return LangchainTool(tool(tool_func))

    def create_tool_bundle(self, tool_config: ToolConfig) -> ToolBundle:
        return LangchainToolBundle(tool_config)
