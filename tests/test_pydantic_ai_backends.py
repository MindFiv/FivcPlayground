from unittest.mock import patch

import pytest

from fivcplayground.backends.pydantic_ai.agents import (
    PydanticAIAgentBackend,
)
from fivcplayground.backends.pydantic_ai.models import PydanticAIModelBackend
from fivcplayground.backends.pydantic_ai.tools import PydanticAIToolBackend
from fivcplayground.cli import _get_backends
from fivcplayground.models.types.base import ModelConfig
from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.base import ToolConfigTransport


class TestPydanticAIModelBackend:
    def test_openai_configuration(self):
        config = ModelConfig(
            id="openai-config",
            provider="openai",
            model="gpt-4o-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.2,
            max_tokens=128,
            enable_thinking=False,
        )

        with patch(
            "fivcplayground.backends.pydantic_ai.models.OpenAIProvider"
        ) as mock_provider, patch(
            "fivcplayground.backends.pydantic_ai.models.OpenAIChatModel"
        ) as mock_model:
            model = PydanticAIModelBackend().create_model(config)

        mock_provider.assert_called_once_with(
            base_url="https://example.com/v1",
            api_key="test-key",
        )
        call_kwargs = mock_model.call_args.kwargs
        assert call_kwargs["provider"] is mock_provider.return_value
        assert call_kwargs["settings"]["temperature"] == 0.2
        assert call_kwargs["settings"]["max_tokens"] == 128
        assert call_kwargs["settings"]["thinking"] is False
        assert model.get_underlying() is mock_model.return_value

    def test_ollama_configuration(self):
        config = ModelConfig(
            id="ollama-config",
            provider="ollama",
            model="qwen3",
            base_url="http://localhost:11434/v1",
            temperature=0.4,
            max_tokens=256,
            enable_thinking=True,
        )

        with patch(
            "fivcplayground.backends.pydantic_ai.models.OllamaProvider"
        ) as mock_provider, patch(
            "fivcplayground.backends.pydantic_ai.models.OllamaModel"
        ) as mock_model:
            model = PydanticAIModelBackend().create_model(config)

        mock_provider.assert_called_once_with(
            base_url="http://localhost:11434/v1",
            api_key=None,
        )
        call_kwargs = mock_model.call_args.kwargs
        assert mock_model.call_args.args == ("qwen3",)
        assert call_kwargs["provider"] is mock_provider.return_value
        assert call_kwargs["settings"]["thinking"] is True
        assert model.get_underlying() is mock_model.return_value

    def test_unsupported_provider(self):
        config = ModelConfig(
            id="unsupported",
            provider="gemini",
            model="gemini-2.5-flash",
        )
        with pytest.raises(ValueError, match="Unsupported model provider: gemini"):
            PydanticAIModelBackend().create_model(config)


class TestPydanticAIToolBackend:
    def test_create_sync_and_async_tools(self):
        async def async_tool(value: str) -> str:
            return value

        def sync_tool(value: str) -> str:
            return value

        backend = PydanticAIToolBackend()
        wrapped_sync = backend.create_tool(
            sync_tool,
            tool_name="renamed",
            tool_description="A renamed tool",
        )
        wrapped_async = backend.create_tool(async_tool)

        assert wrapped_sync.name == "renamed"
        assert wrapped_sync.description == "A renamed tool"
        assert wrapped_sync.get_underlying().function is sync_tool
        assert wrapped_async.get_underlying().function is async_tool

    @pytest.mark.asyncio
    async def test_mcp_stdio_toolset_prefix(self):
        config = ToolConfig(
            id="filesystem",
            description="Filesystem MCP tools",
            transport=ToolConfigTransport.STDIO,
            command="uvx",
            args=["mcp-server-filesystem", "/tmp"],
            env={"HOME": "/tmp"},
        )

        with patch(
            "fivcplayground.backends.pydantic_ai.tools.StdioTransport"
        ) as mock_transport, patch(
            "fivcplayground.backends.pydantic_ai.tools.MCPToolset"
        ) as mock_toolset:
            context = PydanticAIToolBackend().create_tool_bundle(config).setup()
            tools = await context.__aenter__()

        mock_transport.assert_called_once_with(
            command="uvx",
            args=["mcp-server-filesystem", "/tmp"],
            env={"HOME": "/tmp"},
        )
        mock_toolset.assert_called_once_with(mock_transport.return_value)
        mock_toolset.return_value.prefixed.assert_called_once_with("mcp__filesystem_")
        assert len(tools) == 1
        assert tools[0].name == "filesystem"
        assert (
            tools[0].get_underlying() is mock_toolset.return_value.prefixed.return_value
        )

    def test_unsupported_transport(self):
        config = ToolConfig(
            id="bad",
            description="Bad MCP tools",
            transport=ToolConfigTransport.FUNCTION,
        )
        config.transport = "bad"
        with pytest.raises(ValueError, match="Unsupported transport: bad"):
            PydanticAIToolBackend().create_tool_bundle(config).setup()

    def test_function_transport_requires_functions(self):
        config = ToolConfig(
            id="empty",
            description="Empty function bundle",
            transport=ToolConfigTransport.FUNCTION,
        )
        with pytest.raises(ValueError, match="functions' is None or empty"):
            PydanticAIToolBackend().create_tool_bundle(config)


def test_cli_backend_selection():
    model_backend, tool_backend, agent_backend = _get_backends("pydantic_ai")
    assert isinstance(model_backend, PydanticAIModelBackend)
    assert isinstance(tool_backend, PydanticAIToolBackend)
    assert isinstance(agent_backend, PydanticAIAgentBackend)


def test_cli_unknown_backend():
    with pytest.raises(ValueError, match="pydantic_ai"):
        _get_backends("unknown")
