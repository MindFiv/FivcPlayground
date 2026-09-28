"""Tests for the backend-agnostic agent streaming contract."""

import asyncio
import inspect
import tempfile
from datetime import datetime
from collections.abc import AsyncIterator
from typing import get_args, get_origin, get_type_hints
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel
from google.adk.models import BaseLlm as AdkModelUnderlying
from strands.agent import AgentResult as StrandsAgentResult
from strands.telemetry.metrics import EventLoopMetrics

from fivcplayground.agents import AgentConfig
from fivcplayground.agents.types import (
    AgentRun,
    AgentRunContent,
    AgentRunEvent,
    AgentRunRepository,
    AgentRunnable,
    AgentRunStatus,
    AgentRunSession,
    BoundedAgentRunnable,
    ParameterizedAgentRunnable,
)
from fivcplayground.agents.types.base import AgentStructuredOutputError
from fivcplayground.backends.adk.agents import AdkAgentRunnable
from fivcplayground.backends.strands.agents import StrandsAgentRunnable
from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
from fivcplayground.agents.types.repositories.sqlite import SqliteAgentRunRepository
from fivcplayground.utils import OutputDir


class AnswerResponse(BaseModel):
    answer: int


def _make_strands_agent() -> StrandsAgentRunnable:
    config = AgentConfig(
        id="test-agent",
        description="Test agent",
        system_prompt="You are a test agent",
    )
    return StrandsAgentRunnable(config, Mock())


def _make_strands_result(text: str) -> StrandsAgentResult:
    return StrandsAgentResult(
        stop_reason="end_turn",
        message={"role": "assistant", "content": [{"text": text}]},
        metrics=EventLoopMetrics(),
        state={},
    )


def _make_adk_agent() -> AdkAgentRunnable:
    config = AgentConfig(
        id="test_agent",
        model_id="test-model",
        system_prompt="You are a test agent",
    )
    return AdkAgentRunnable(config, Mock(spec=AdkModelUnderlying))


def _make_adk_event(text: str = "", final: bool = False) -> Mock:
    event = Mock()
    part = Mock()
    part.text = text
    part.function_call = None
    part.function_response = None
    event.content.parts = [part] if text else []
    event.content = event.content
    event.get_function_calls.return_value = []
    event.get_function_responses.return_value = []
    event.is_final_response.return_value = final
    return event


class TestStreamContract:
    def test_agent_runnable_stream_type_contract(self):
        hints = get_type_hints(AgentRunnable.stream_async)
        assert get_origin(hints["return"]) is AsyncIterator
        assert get_args(hints["return"]) == (tuple[AgentRunEvent, AgentRun],)

    @pytest.mark.asyncio
    async def test_strands_is_an_async_generator(self):
        assert inspect.isasyncgenfunction(StrandsAgentRunnable.stream_async)
        assert inspect.isasyncgenfunction(AdkAgentRunnable.stream_async)

    def test_sort_helper_is_not_public(self):
        import fivcplayground.agents.types as agent_types

        assert not hasattr(agent_types, "agent_run_chronological_sort_key")
        assert "agent_run_chronological_sort_key" not in agent_types.__all__


class TestStrandsStream:
    @pytest.mark.asyncio
    async def test_stream_maps_events_and_emits_snapshots(self):
        agent = _make_strands_agent()
        underlying = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"data": "Hel"}
            yield {"message": {"content": [{"text": "lo"}]}}
            yield {"result": _make_strands_result("Hello")}

        underlying.stream_async = mock_stream

        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying",
            return_value=underlying,
        ):
            events = []
            async for event, run in agent.stream_async(query="test"):
                events.append((event, run))

        assert [event for event, _ in events] == [
            AgentRunEvent.START,
            AgentRunEvent.STREAM,
            AgentRunEvent.UPDATE,
            AgentRunEvent.FINISH,
        ]
        assert events[0][1] is not events[1][1]
        assert events[1][1].delta is not None
        assert events[1][1].delta.text == "Hel"
        assert events[-1][1].status == AgentRunStatus.COMPLETED
        assert events[-1][1].reply is not None
        assert events[-1][1].reply.text == "Hello\n"

    def test_stream_contract_has_no_callback(self):
        stream_params = inspect.signature(AgentRunnable.stream_async).parameters.keys()
        run_params = inspect.signature(AgentRunnable.run_async).parameters.keys()

        assert "event_callback" not in stream_params
        assert "event_callback" in run_params

    @pytest.mark.asyncio
    async def test_stream_runtime_error_emits_finish_then_raises(self):
        agent = _make_strands_agent()
        underlying = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"data": "partial"}
            raise RuntimeError("boom")

        underlying.stream_async = mock_stream

        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying",
            return_value=underlying,
        ):
            stream = agent.stream_async(query="test")
            events = []
            with pytest.raises(RuntimeError, match="boom"):
                async for item in stream:
                    events.append(item)

        assert events[-1][0] == AgentRunEvent.FINISH
        assert events[-1][1].status == AgentRunStatus.FAILED
        assert "boom" in events[-1][1].error

    @pytest.mark.asyncio
    async def test_run_async_raises_runtime_error(self):
        agent = _make_strands_agent()
        underlying = AsyncMock()

        async def mock_stream(*args, **kwargs):
            raise RuntimeError("boom")
            yield  # pragma: no cover - makes this mock an async generator

        underlying.stream_async = mock_stream

        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying",
            return_value=underlying,
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await agent.run_async(query="test")

    @pytest.mark.asyncio
    async def test_stream_structured_parse_error_emits_finish_then_raises(self):
        agent = _make_strands_agent()
        underlying = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"result": _make_strands_result("not-json")}

        underlying.stream_async = mock_stream

        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying",
            return_value=underlying,
        ):
            stream = agent.stream_async(query="test", response_model=AnswerResponse)
            events = []
            with pytest.raises(AgentStructuredOutputError):
                async for item in stream:
                    events.append(item)

        assert events[-1][1].status == AgentRunStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_async_raises_structured_parse_error(self):
        agent = _make_strands_agent()
        underlying = AsyncMock()

        async def mock_stream(*args, **kwargs):
            yield {"result": _make_strands_result("not-json")}

        underlying.stream_async = mock_stream

        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying",
            return_value=underlying,
        ):
            with pytest.raises(AgentStructuredOutputError):
                await agent.run_async(query="test", response_model=AnswerResponse)


class TestAdkStream:
    @pytest.mark.asyncio
    async def test_stream_maps_events_and_emits_snapshots(self):
        agent = _make_adk_agent()
        runner = Mock()

        async def mock_run(*args, **kwargs):
            yield _make_adk_event("Hel")
            yield _make_adk_event("Hello", final=True)

        runner.run_async = mock_run

        with patch("fivcplayground.backends.adk.agents.Runner", return_value=runner):
            events = []
            async for event, run in agent.stream_async(query="test"):
                events.append((event, run))

        assert [event for event, _ in events] == [
            AgentRunEvent.START,
            AgentRunEvent.STREAM,
            AgentRunEvent.UPDATE,
            AgentRunEvent.FINISH,
        ]
        assert events[0][1] is not events[1][1]
        assert events[-1][1].status == AgentRunStatus.COMPLETED
        assert events[-1][1].reply is not None
        assert events[-1][1].reply.text == "Hello"

    @pytest.mark.asyncio
    async def test_stream_runtime_error_emits_finish_then_raises(self):
        agent = _make_adk_agent()
        runner = Mock()

        async def mock_run(*args, **kwargs):
            yield _make_adk_event("partial")
            raise RuntimeError("boom")

        runner.run_async = mock_run

        with patch("fivcplayground.backends.adk.agents.Runner", return_value=runner):
            stream = agent.stream_async(query="test")
            events = []
            with pytest.raises(RuntimeError, match="boom"):
                async for item in stream:
                    events.append(item)

        assert events[-1][0] == AgentRunEvent.FINISH
        assert events[-1][1].status == AgentRunStatus.FAILED
        assert "boom" in events[-1][1].error

    @pytest.mark.asyncio
    async def test_stream_structured_parse_error_emits_finish_then_raises(self):
        agent = _make_adk_agent()
        runner = Mock()
        runner_kwargs = {}

        def make_runner(*args, **kwargs):
            runner_kwargs.update(kwargs)
            return runner

        async def mock_run(*args, **kwargs):
            generate = runner_kwargs["agent"].tools[-1]
            generate({"unexpected": "value"})
            yield  # pragma: no cover - makes this mock an async generator

        runner.run_async = mock_run

        with patch(
            "fivcplayground.backends.adk.agents.Runner", side_effect=make_runner
        ):
            stream = agent.stream_async(query="test", response_model=AnswerResponse)
            events = []
            with pytest.raises(AgentStructuredOutputError):
                async for item in stream:
                    events.append(item)

        assert events[-1][0] == AgentRunEvent.FINISH
        assert events[-1][1].status == AgentRunStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_async_raises_structured_parse_error(self):
        agent = _make_adk_agent()
        runner = Mock()
        runner_kwargs = {}

        def make_runner(*args, **kwargs):
            runner_kwargs.update(kwargs)
            return runner

        async def mock_run(*args, **kwargs):
            generate = runner_kwargs["agent"].tools[-1]
            generate({"unexpected": "value"})
            yield  # pragma: no cover - makes this mock an async generator

        runner.run_async = mock_run

        with patch(
            "fivcplayground.backends.adk.agents.Runner", side_effect=make_runner
        ):
            with pytest.raises(AgentStructuredOutputError):
                await agent.run_async(query="test", response_model=AnswerResponse)

    @pytest.mark.asyncio
    async def test_closing_stream_persists_failed_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileAgentRunRepository(output_dir=OutputDir(tmpdir))
            session_id = "stream-session"
            agent = _make_adk_agent()
            runner = Mock()
            first_event = _make_adk_event("partial")
            runner_finished = asyncio.Event()

            async def mock_run(*args, **kwargs):
                try:
                    yield first_event
                    await asyncio.Event().wait()
                finally:
                    runner_finished.set()

            runner.run_async = mock_run

            with patch(
                "fivcplayground.backends.adk.agents.Runner", return_value=runner
            ):
                stream = agent.stream_async(
                    query="test",
                    agent_run_repository=repository,
                    agent_run_session_id=session_id,
                )
                _, run = await stream.__anext__()
                await stream.__anext__()
                await stream.aclose()

            await asyncio.wait_for(runner_finished.wait(), timeout=1)
            persisted = await repository.get_agent_run_async(session_id, run.id)
            assert persisted is not None
            assert persisted.status == AgentRunStatus.FAILED
            assert "cancelled" in persisted.error.lower()


class TestRunnableWrappers:
    @pytest.mark.asyncio
    async def test_bounded_stream_merges_defaults(self):
        run = AgentRun(agent_id="inner")
        inner = Mock()
        call_kwargs = {}

        async def inner_stream(**kwargs):
            call_kwargs.update(kwargs)
            yield AgentRunEvent.START, run

        inner.stream_async = Mock(side_effect=inner_stream)
        wrapper = BoundedAgentRunnable(inner, model_id="default")

        events = [event async for event, _ in wrapper.stream_async(query="hello")]

        assert events == [AgentRunEvent.START]
        inner.stream_async.assert_called_once_with(query="hello", model_id="default")

    @pytest.mark.asyncio
    async def test_parameterized_stream_formats_query(self):
        run = AgentRun(agent_id="inner")
        inner = Mock()
        call_kwargs = {}

        async def inner_stream(**kwargs):
            call_kwargs.update(kwargs)
            yield AgentRunEvent.START, run

        inner.stream_async = Mock(side_effect=inner_stream)
        wrapper = ParameterizedAgentRunnable(inner, "Search: {query} in {topic}")

        events = [
            event
            async for event, _ in wrapper.stream_async(
                query="agents",
                query_params={"topic": "AI"},
                response_model=AnswerResponse,
            )
        ]

        assert events == [AgentRunEvent.START]
        inner.stream_async.assert_called_once_with(
            query="Search: agents in AI",
            response_model=AnswerResponse,
        )


class TestRepositoryChronologicalOrder:
    @staticmethod
    async def _create_session(repository: AgentRunRepository) -> AgentRunSession:
        session = AgentRunSession(agent_id="sort-agent")
        await repository.update_agent_run_session_async(session)
        return session

    @staticmethod
    def _runs() -> list[AgentRun]:
        return [
            AgentRun(
                id="invalid",
                agent_id="sort-agent",
                query=AgentRunContent(text="invalid"),
            ),
            AgentRun(
                id="1700000100",
                agent_id="sort-agent",
                query=AgentRunContent(text="legacy"),
            ),
            AgentRun(
                id="late",
                agent_id="sort-agent",
                started_at=datetime(2024, 1, 2),
                query=AgentRunContent(text="late"),
            ),
            AgentRun(
                id="b-tie",
                agent_id="sort-agent",
                started_at=datetime(2024, 1, 1),
                query=AgentRunContent(text="b"),
            ),
            AgentRun(
                id="a-tie",
                agent_id="sort-agent",
                started_at=datetime(2024, 1, 1),
                query=AgentRunContent(text="a"),
            ),
        ]

    async def _assert_order(self, repository: AgentRunRepository, session_id: str):
        for run in reversed(self._runs()):
            await repository.update_agent_run_async(session_id, run)

        runs = await repository.list_agent_runs_async(session_id)
        assert [run.id for run in runs] == [
            "1700000100",
            "a-tie",
            "b-tie",
            "late",
            "invalid",
        ]

    @pytest.mark.asyncio
    async def test_file_repository_sorts_runs_chronologically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileAgentRunRepository(output_dir=OutputDir(tmpdir))
            session = await self._create_session(repository)
            await self._assert_order(repository, session.id)

    @pytest.mark.asyncio
    async def test_sqlite_repository_sorts_runs_chronologically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = SqliteAgentRunRepository(output_dir=OutputDir(tmpdir))
            try:
                session = await self._create_session(repository)
                await self._assert_order(repository, session.id)
            finally:
                repository.close()
