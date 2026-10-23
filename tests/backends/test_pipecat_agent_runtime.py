"""Transport lifecycle and run-session tests for the Pipecat agent adapter."""

from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fivcplayground.agents import (
    AgentConfig,
    AgentRun,
    AgentRunContent,
    AgentRunStatus,
)
from fivcplayground.backends.pipecat.agents import (
    PipecatAgentRunnable,
    _PipecatRunSession,
)
from fivcplayground.backends.pipecat.transports import StdioTransport
from pipecat.pipeline.worker import PipelineParams
from pipecat.processors.aggregators.llm_response_universal import (
    LLMAssistantAggregator,
    LLMUserAggregator,
)


def _passthrough_event_handler(name):
    def decorator(handler):
        return handler

    return decorator


def _mock_transport():
    transport = Mock()
    transport.event_handler = _passthrough_event_handler
    transport.input.return_value = Mock(name="transport-input")
    transport.output.return_value = Mock(name="transport-output")
    return transport


def _mock_llm():
    class _FakeSettings:
        def __init__(self, **kwargs):
            pass

    llm = Mock(name="llm")
    llm.event_handler = _passthrough_event_handler
    llm._settings = _FakeSettings()
    llm._update_settings = AsyncMock()
    return llm


class TestPipecatAgentRunnable:
    def make_agent(self):
        return PipecatAgentRunnable(
            AgentConfig(
                id="voice-agent",
                system_prompt="You are helpful.",
                extra={
                    "pipeline_params": {"enable_metrics": True},
                    "idle_timeout_secs": 120,
                },
            ),
            model=_mock_llm(),
        )

    def test_streaming_is_not_supported(self):
        agent = self.make_agent()

        with pytest.raises(NotImplementedError, match="run_async"):
            agent.stream_async()

    @pytest.mark.asyncio
    async def test_none_transport_uses_stdio_and_ignores_stt_tts(self):
        agent = self.make_agent()
        stt, tts = Mock(name="stt"), Mock(name="tts")

        with (
            patch(
                "fivcplayground.backends.pipecat.agents.PipelineWorker"
            ) as worker_cls,
            patch("fivcplayground.backends.pipecat.agents.WorkerRunner") as runner_cls,
            patch("sys.stdin", StringIO("")),
            patch("sys.stdout", StringIO()),
        ):
            runner = runner_cls.return_value
            runner.add_workers = AsyncMock()
            runner.run = AsyncMock()
            runner.cancel = AsyncMock()

            result = await agent.run_async(stt=stt, tts=tts)

        assert isinstance(result, AgentRunContent)
        processors = worker_cls.call_args.args[0].processors[1:-1]
        assert stt not in processors
        assert tts not in processors
        assert type(processors[0]).__name__ == "_StdioInputProcessor"
        assert isinstance(processors[1], LLMUserAggregator)
        assert processors[2] is agent._agent_model
        assert type(processors[3]).__name__ == "_StdioOutputProcessor"
        assert isinstance(processors[4], LLMAssistantAggregator)

    @pytest.mark.asyncio
    async def test_runs_transport_pipeline_until_runner_completes(self):
        agent = self.make_agent()
        transport = _mock_transport()
        stt, tts = Mock(), Mock()

        with (
            patch(
                "fivcplayground.backends.pipecat.agents.PipelineWorker"
            ) as worker_cls,
            patch("fivcplayground.backends.pipecat.agents.WorkerRunner") as runner_cls,
        ):
            runner = runner_cls.return_value
            runner.add_workers = AsyncMock()
            runner.run = AsyncMock()
            runner.cancel = AsyncMock()

            result = await agent.run_async(transport=transport, stt=stt, tts=tts)

        runner.add_workers.assert_awaited_once_with(worker_cls.return_value)
        runner.run.assert_awaited_once_with()
        assert isinstance(result, AgentRunContent)
        assert result.text == ""

        worker_args = worker_cls.call_args.args
        worker_kwargs = worker_cls.call_args.kwargs
        assert len(worker_args) == 1
        assert worker_kwargs["params"] == PipelineParams(enable_metrics=True)
        assert worker_kwargs["idle_timeout_secs"] == 120
        processors = worker_args[0].processors[1:-1]
        assert processors[0] is transport.input.return_value
        assert processors[1] is stt
        assert isinstance(processors[2], LLMUserAggregator)
        assert processors[3] is agent._agent_model
        assert processors[4] is tts
        assert processors[5] is transport.output.return_value
        assert isinstance(processors[6], LLMAssistantAggregator)


class TestPipecatRunSession:
    @pytest.mark.asyncio
    async def test_user_and_assistant_turns_persist(self):
        saved: list[AgentRun] = []

        class Span:
            async def __call__(self, run: AgentRun, **kwargs):
                saved.append(run.model_copy(deep=True))

        session = _PipecatRunSession("voice", Span())
        await session.on_user_turn("hello")
        assert session.current is not None
        assert session.current.query.text == "hello"
        assert session.current.status == AgentRunStatus.EXECUTING

        await session.on_assistant_turn("hi there")
        assert session.current is None
        assert session.last is not None
        assert session.last.reply.text == "hi there"
        assert session.last.status == AgentRunStatus.COMPLETED
        assert len(saved) == 2


class TestStdioTransport:
    @pytest.mark.asyncio
    async def test_eof_without_pending_response_disconnects(self):
        transport = StdioTransport(
            input_stream=StringIO(""),
            output_stream=StringIO(),
        )
        disconnected = []

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(t, client):
            disconnected.append((t, client))

        await transport.notify_eof()
        assert len(disconnected) == 1
        assert disconnected[0][0] is transport

    @pytest.mark.asyncio
    async def test_eof_waits_for_response_before_disconnect(self):
        transport = StdioTransport(
            input_stream=StringIO("hi\n"),
            output_stream=StringIO(),
        )
        disconnected = []

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(t, client):
            disconnected.append(t)

        transport.mark_user_turn_sent()
        await transport.notify_eof()
        assert disconnected == []

        await transport.notify_response_done()
        assert disconnected == [transport]
