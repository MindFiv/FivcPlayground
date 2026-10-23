"""Pipecat tool backend implementations."""

import inspect
from collections.abc import Callable
from typing import Any

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
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.mcp_service import MCPClient


def _json_type(annotation: Any) -> str:
    if annotation in (str, "str"):
        return "string"
    if annotation in (int, "int"):
        return "integer"
    if annotation in (float, "float"):
        return "number"
    if annotation in (bool, "bool"):
        return "boolean"
    return "string"


def _make_handler(func: Callable):
    async def handler(params: FunctionCallParams) -> None:
        result = func(**dict(params.arguments))
        if inspect.isawaitable(result):
            result = await result
        await params.result_callback(result)

    return handler


class PipecatTool(Tool):
    """A Pipecat function schema exposed through the Tool contract."""

    def __init__(self, schema: FunctionSchema):
        self._schema = schema

    @property
    def name(self) -> str:
        return self._schema.name

    @property
    def description(self) -> str:
        return self._schema.description

    def get_underlying(self) -> FunctionSchema:
        return self._schema


class PipecatToolBundleContext(ToolBundleContext):
    """Expand an MCP server into Pipecat function schemas."""

    def __init__(self, client: MCPClient):
        self._client = client

    async def __aenter__(self) -> list[Tool]:
        tools_schema = await self._client.tools()
        return [PipecatTool(schema) for schema in tools_schema.standard_tools]

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._client.close()


class PipecatToolBundle(ToolBundle):
    """A Pipecat-backed MCP tool bundle."""

    def __init__(self, tool_config: ToolConfig):
        self._tool_config = tool_config

    @property
    def name(self) -> str:
        return self._tool_config.id

    @property
    def description(self) -> str:
        return self._tool_config.description

    def get_underlying(self) -> Any:
        return self._tool_config

    def setup(self, **context: Any) -> ToolBundleContext:
        del context
        config = self._tool_config
        if config.transport == ToolConfigTransport.STDIO:
            from mcp import StdioServerParameters

            params = StdioServerParameters(
                command=config.command, args=config.args, env=config.env
            )
        elif config.transport == ToolConfigTransport.SSE:
            from mcp.client.session_group import SseServerParameters

            params = SseServerParameters(url=config.url)
        elif config.transport == ToolConfigTransport.STREAMABLE_HTTP:
            from mcp.client.session_group import StreamableHttpParameters

            params = StreamableHttpParameters(url=config.url)
        else:
            raise ValueError(f"Unsupported MCP transport: {config.transport}")
        return PipecatToolBundleContext(MCPClient(server_params=params))


class PipecatToolBackend(ToolBackend):
    """Create Pipecat function schemas and MCP bundles."""

    def create_tool(
        self,
        tool_func: Callable,
        tool_name: str | None = None,
        tool_description: str | None = None,
    ) -> Tool:
        name = tool_name or getattr(tool_func, "__name__", "tool")
        description = tool_description or inspect.getdoc(tool_func) or ""
        signature = inspect.signature(tool_func)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for parameter_name, parameter in signature.parameters.items():
            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            properties[parameter_name] = {
                "type": _json_type(parameter.annotation),
            }
            if parameter.default is inspect.Parameter.empty:
                required.append(parameter_name)

        return PipecatTool(
            FunctionSchema(
                name=name,
                description=description,
                properties=properties,
                required=required,
                handler=_make_handler(tool_func),
            )
        )

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
        return PipecatToolBundle(tool_config)
