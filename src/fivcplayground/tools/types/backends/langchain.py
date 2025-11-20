__all__ = [
    "make_tool",
    "get_tool_name",
    "get_tool_description",
    "set_tool_description",
    "Tool",
    "FuncTool",
    "ToolBundle",
]

from contextlib import asynccontextmanager
from typing import List, AsyncGenerator

from langchain_core.tools import (
    tool as make_tool,
    BaseTool as Tool,
    Tool as FuncTool,
)

from langchain_mcp_adapters.sessions import create_session
from langchain_mcp_adapters.tools import load_mcp_tools

from fivcplayground.tools.types.base import ToolConfig


class ToolBundle(FuncTool):
    """MCP tools bundle"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(
            name=tool_config.id,
            func=None,
            description=tool_config.description,
        )
        # Store tools using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "_config", tool_config)

    @asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        config = object.__getattribute__(self, "_config")
        if config.transport == "stdio":
            from langchain_mcp_adapters.sessions import StdioConnection

            conn = StdioConnection(
                transport="stdio",
                command=config.command,
                args=config.args,
                env=config.env,
            )
        elif config.transport == "sse":
            from langchain_mcp_adapters.sessions import SSEConnection

            conn = SSEConnection(
                transport="sse",
                url=config.url,
            )
        elif config.transport == "streamable_http":
            from langchain_mcp_adapters.sessions import StreamableHttpConnection

            conn = StreamableHttpConnection(
                transport="streamable_http",
                url=config.url,
            )
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")

        async with create_session(conn) as session:
            await session.initialize()
            yield await load_mcp_tools(session)


def get_tool_name(tool: Tool) -> str:
    """Get the name of a tool."""
    return tool.name


def get_tool_description(tool: Tool) -> str:
    """Get the description of a tool."""
    return tool.description


def set_tool_description(tool: Tool, description: str):
    """Set the description of a tool."""
    tool.description = description
