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
from typing import List, Any, AsyncGenerator
from uuid import uuid4

from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
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


def _tool_bundle_func(*args: Any, **kwargs: Any) -> ToolResult:
    return ToolResult(content=[], status="success", toolUseId=str(uuid4()))


class ToolsBundle(FuncTool):
    """MCP tools bundle"""

    def __init__(self, name: str, conn: dict):
        super().__init__(
            name,
            ToolSpec(
                description="MCP tools bundle",
                inputSchema={},
                name=name,
            ),
            _tool_bundle_func,
        )
        self._conn = conn

    @asynccontextmanager
    async def load_async(self) -> AsyncGenerator[List[Tool], None]:
        if "command" in self._conn:
            c = stdio_client(StdioServerParameters(**self._conn))
        else:
            self._conn.pop("transport", None)  # remove transport
            c = sse_client(**self._conn)

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
