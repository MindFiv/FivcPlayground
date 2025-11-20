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
from typing import List, Any, AsyncGenerator
from uuid import uuid4

from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

from strands.types.tools import (
    AgentTool as Tool,
    ToolSpec,
    ToolResult,
)
from strands.tools import (
    tool as make_tool,
    PythonAgentTool as FuncTool,
)
from fivcplayground.tools.types.base import ToolConfig


def _tool_bundle_func(*args: Any, **kwargs: Any) -> ToolResult:
    return ToolResult(content=[], status="success", toolUseId=str(uuid4()))


class ToolBundle(FuncTool):
    """MCP tools bundle"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(
            tool_config.id,
            ToolSpec(
                description=tool_config.description,
                inputSchema={},
                name=tool_config.id,
            ),
            _tool_bundle_func,
        )
        self._config = tool_config

    @asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        if self._config.transport == "stdio":
            c = stdio_client(
                StdioServerParameters(
                    command=self._config.command,
                    args=self._config.args,
                    env=self._config.env,
                )
            )
        elif self._config.transport == "sse":
            c = sse_client(url=self._config.url)
        elif self._config.transport == "streamable_http":
            c = streamablehttp_client(url=self._config.url)
        else:
            raise ValueError(f"Unsupported transport: {self._config.transport}")

        with MCPClient(lambda: c) as client:
            tools = client.list_tools_sync()
            yield list(tools)


def get_tool_name(tool: Tool) -> str:
    """Get the name of a tool."""
    return tool.tool_name


def get_tool_description(tool: Tool) -> str:
    """Get the description of a tool."""
    return tool.tool_spec.get("description") or ""


def set_tool_description(tool: Tool, description: str):
    """Set the description of a tool."""
    tool.tool_spec["description"] = description
