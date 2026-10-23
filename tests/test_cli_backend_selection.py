"""Tests for selectable runtime agent backends."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fivcplayground.backends.pipecat.transports import StdioTransport
from fivcplayground.cli import _get_backends, _run_async


class TestBackendSelection:
    @pytest.mark.parametrize("backend", ["pipecat"])
    def test_selects_matching_backend_triple(self, backend):
        model_backend, tool_backend, agent_backend = _get_backends(backend)

        assert (
            type(model_backend).__name__
            == {
                "strands": "StrandsModelBackend",
                "adk": "AdkModelBackend",
                "pipecat": "PipecatModelBackend",
            }[backend]
        )
        assert type(tool_backend).__name__.endswith("ToolBackend")
        assert type(agent_backend).__name__.endswith("AgentBackend")

    def test_unknown_backend_is_rejected(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            _get_backends("unknown")

    @pytest.mark.asyncio
    async def test_cli_pipecat_query_uses_stdio_transport(self):
        agent = MagicMock()
        agent.run_async = AsyncMock(
            return_value=MagicMock(model_dump_json=lambda: "{}")
        )

        with (
            patch("fivcplayground.cli.create_builtin_tools_async", new=AsyncMock()),
            patch(
                "fivcplayground.cli.create_tool_retriever_async",
                new=AsyncMock(return_value=MagicMock()),
            ),
            patch(
                "fivcplayground.cli.create_agent_async",
                new=AsyncMock(return_value=agent),
            ),
            patch("fivcplayground.cli.FileModelConfigRepository"),
            patch("fivcplayground.cli.FileToolConfigRepository"),
            patch("fivcplayground.cli.FileEmbeddingConfigRepository"),
            patch("fivcplayground.cli.FileAgentConfigRepository"),
            patch("fivcplayground.backends.chroma.ChromaEmbeddingBackend"),
            patch("fivcplayground.cli._get_backends") as get_backends,
        ):
            get_backends.return_value = (MagicMock(), MagicMock(), MagicMock())
            await _run_async(
                agent_name="Generic",
                query="hello",
                output=None,
                dry_run=False,
                verbose=False,
                backend="pipecat",
            )

        agent.run_async.assert_awaited_once()
        kwargs = agent.run_async.await_args.kwargs
        assert isinstance(kwargs["transport"], StdioTransport)
