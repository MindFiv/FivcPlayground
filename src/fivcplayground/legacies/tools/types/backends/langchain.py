__all__ = [
    "make_tool",
    "get_tool_name",
    "get_tool_description",
    "set_tool_description",
    "Tool",
    "FuncTool",
    "ToolsBundle",
]

from contextlib import asynccontextmanager
from typing import List, AsyncGenerator

from langchain_core.tools import (
    tool as make_tool,
    BaseTool as Tool,
    Tool as FuncTool,
)

# from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import create_session
from langchain_mcp_adapters.tools import load_mcp_tools


class ToolsBundle(FuncTool):
    """MCP tools bundle"""

    def __init__(self, name: str, conn: dict):
        super().__init__(name=name, func=None, description="")
        # Store tools using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "_conn", conn)

    @asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        async with create_session(self.conn) as session:
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
