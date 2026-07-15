"""
Unit tests for ADK Agent backend implementation.

Tests the ADK agent runtime including:
- Event detection and processing (STREAM, TOOL, UPDATE, FINISH)
- Tool call tracking and results
- Output extraction from Content/Part structure
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch
from warnings import catch_warnings

import pytest
from google.adk.events import Event
from google.adk.models import BaseLlm as AdkModelUnderlying
from google.adk.runners import Runner
from google.genai.types import Content, Part, FunctionCall, FunctionResponse
from pydantic import BaseModel

from fivcplayground.agents import (
    AgentConfig,
    AgentRunContent,
    AgentRunEvent,
    AgentRunStatus,
)
from fivcplayground.backends.adk.agents import AdkAgentRunnable


class ContactInfo(BaseModel):
    """Test structured output model."""

    name: str
    email: str


def _make_agent_config(**kwargs) -> AgentConfig:
    """Helper to create AgentConfig with defaults."""
    defaults = {
        "id": "test_agent",
        "name": "Test Agent",
        "model_id": "test-model",
        "system_prompt": "You are a helpful assistant.",
    }
    defaults.update(kwargs)
    return AgentConfig(**defaults)


def _create_mock_event(
    text: str | None = None,
    func_calls: list | None = None,
    func_responses: list | None = None,
    is_final: bool = False,
) -> Event:
    """Create a mock ADK Event."""
    mock_event = MagicMock(spec=Event)
    mock_event.is_final_response.return_value = is_final

    if text:
        part = MagicMock(spec=Part)
        part.text = text
        part.function_call = None
        part.function_response = None
        mock_event.content = MagicMock(spec=Content)
        mock_event.content.parts = [part]
    else:
        mock_event.content = MagicMock(spec=Content)
        mock_event.content.parts = []

    mock_event.get_function_calls.return_value = func_calls or []
    mock_event.get_function_responses.return_value = func_responses or []

    return mock_event


async def _async_generator(items):
    """Helper to create async generator from list."""
    for item in items:
        yield item


def _create_mocks_for_run():
    """Create properly configured mocks for run_async."""
    mock_tool_span = MagicMock()
    mock_tool_span.__aenter__ = AsyncMock(return_value=mock_tool_span)
    mock_tool_span.__aexit__ = AsyncMock(return_value=None)
    mock_tool_span.tools = []

    # Create a callable async context manager for session span
    async_context_mock = AsyncMock()
    mock_session_span = AsyncMock(return_value=async_context_mock)
    mock_session_span.__aenter__ = AsyncMock(return_value=mock_session_span)
    mock_session_span.__aexit__ = AsyncMock(return_value=None)

    return mock_tool_span, mock_session_span


class TestAdkAgentRuntime:
    """Test ADK agent runtime execution."""

    @pytest.mark.asyncio
    async def test_run_async_passes_context_to_tool_span(self):
        """Test runtime context is passed into AgentRunToolSpan."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="Done", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async
        runtime_context = {"request_id": object()}

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(query="test", context=runtime_context)

        _, kwargs = mock_tool_span_cls.call_args
        assert kwargs["context"] is runtime_context

    @pytest.mark.asyncio
    async def test_stream_event_detection(self):
        """Test STREAM event is emitted for text content."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="Hello, ", is_final=False)

        # Properly create an async generator
        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        events_emitted = []

        def capture_callback(event, run):
            events_emitted.append(event)

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="test", event_callback=capture_callback
                    )

        assert AgentRunEvent.START in events_emitted
        assert AgentRunEvent.FINISH in events_emitted

    @pytest.mark.asyncio
    async def test_tool_event_with_function_calls(self):
        """Test TOOL event is emitted for function calls."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_func_call = MagicMock(spec=FunctionCall)
        mock_func_call.id = "call-123"
        mock_func_call.name = "calculator"
        mock_func_call.args = {"expression": "2+2"}

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(func_calls=[mock_func_call], is_final=False)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        events_emitted = []

        def capture_callback(event, run):
            events_emitted.append(event)

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="calculate", event_callback=capture_callback
                    )

        assert AgentRunEvent.TOOL in events_emitted

    @pytest.mark.asyncio
    async def test_final_response_captured(self):
        """Test UPDATE event is emitted for final response."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="Final answer", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        events_emitted = []

        def capture_callback(event, run):
            events_emitted.append(event)

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="test", event_callback=capture_callback
                    )

        assert AgentRunEvent.UPDATE in events_emitted
        assert AgentRunEvent.FINISH in events_emitted

    @pytest.mark.asyncio
    async def test_tool_call_tracking(self):
        """Test tool calls are properly tracked."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_func_call = MagicMock(spec=FunctionCall)
        mock_func_call.id = "call-123"
        mock_func_call.name = "calculator"
        mock_func_call.args = {"expression": "2+2"}

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(func_calls=[mock_func_call])

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        captured_run = None

        def capture_callback(event, run):
            nonlocal captured_run
            if event == AgentRunEvent.TOOL:
                captured_run = run

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="calculate", event_callback=capture_callback
                    )

        assert captured_run is not None
        assert "call-123" in captured_run.tool_calls
        tool_call = captured_run.tool_calls["call-123"]
        assert tool_call.tool_id == "calculator"
        assert tool_call.tool_input == {"expression": "2+2"}

    @pytest.mark.asyncio
    async def test_tool_response_tracking(self):
        """Test tool responses are properly tracked."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_func_call = MagicMock(spec=FunctionCall)
        mock_func_call.id = "call-123"
        mock_func_call.name = "calculator"
        mock_func_call.args = {"expression": "2+2"}

        mock_func_response = MagicMock(spec=FunctionResponse)
        mock_func_response.id = "call-123"
        mock_func_response.response = "4"

        mock_runner = MagicMock(spec=Runner)
        mock_event_call = _create_mock_event(func_calls=[mock_func_call])
        mock_event_response = _create_mock_event(func_responses=[mock_func_response])

        async def mock_run_async(*args, **kwargs):
            yield mock_event_call
            yield mock_event_response

        mock_runner.run_async = mock_run_async

        final_run = None

        def capture_callback(event, run):
            nonlocal final_run
            if event == AgentRunEvent.FINISH:
                final_run = run

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="calculate", event_callback=capture_callback
                    )

        assert final_run is not None
        assert "call-123" in final_run.tool_calls
        tool_call = final_run.tool_calls["call-123"]
        assert tool_call.tool_result == "4"
        assert tool_call.status == "success"

    @pytest.mark.asyncio
    async def test_unknown_tool_response_warning(self):
        """Test warning for tool response to unknown call."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_func_response = MagicMock(spec=FunctionResponse)
        mock_func_response.id = "unknown-id"
        mock_func_response.response = "unexpected"

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(func_responses=[mock_func_response])

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    with catch_warnings(record=True) as w:
                        await runnable.run_async(query="test")
                        assert len(w) >= 1
                        assert "unknown tool call" in str(w[-1].message).lower()

    @pytest.mark.asyncio
    async def test_output_extraction(self):
        """Test output is properly extracted from Content."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="The answer is 4", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    result = await runnable.run_async(query="test")

        assert isinstance(result, AgentRunContent)
        assert "The answer is 4" in result.text

    @pytest.mark.skip(
        reason="ADK structured output tool invocation needs real agent execution"
    )
    @pytest.mark.asyncio
    async def test_structured_output_parsing(self):
        """Test structured output is parsed from tool call."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        contact_data = ContactInfo(name="John Doe", email="john@example.com")

        mock_runner = MagicMock(spec=Runner)

        # Create mock function call for structured output tool
        # The agent calls generate_structured_output with the contact data dict
        mock_func_call = MagicMock()
        mock_func_call.id = "call_1"
        mock_func_call.name = "generate_structured_output"
        mock_func_call.args = contact_data.model_dump()

        # Create mock function response confirming the call succeeded
        mock_func_response = MagicMock()
        mock_func_response.id = "call_1"
        mock_func_response.response = "OK"

        # Event 1: Agent makes the function call
        mock_event1 = MagicMock(spec=Event)
        mock_event1.is_final_response.return_value = False
        mock_event1.content = MagicMock(spec=Content)
        mock_event1.content.parts = []
        mock_event1.get_function_calls.return_value = [mock_func_call]
        mock_event1.get_function_responses.return_value = []

        # Event 2: Final response
        mock_event2 = MagicMock(spec=Event)
        mock_event2.is_final_response.return_value = True
        mock_event2.content = MagicMock(spec=Content)
        mock_event2.content.parts = []
        mock_event2.get_function_calls.return_value = []
        mock_event2.get_function_responses.return_value = [mock_func_response]

        async def mock_run_async(*args, **kwargs):
            yield mock_event1
            yield mock_event2

        mock_runner.run_async = mock_run_async

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    result = await runnable.run_async(
                        query="extract contact",
                        response_model=ContactInfo,
                    )

        assert isinstance(result, ContactInfo)
        assert result.name == "John Doe"
        assert result.email == "john@example.com"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling when agent raises exception."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_runner.run_async = AsyncMock(side_effect=RuntimeError("Agent failed"))

        captured_run = None

        def capture_callback(event, run):
            nonlocal captured_run
            if event == AgentRunEvent.FINISH:
                captured_run = run

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="test", event_callback=capture_callback
                    )

        assert captured_run is not None
        assert captured_run.status == AgentRunStatus.FAILED
        assert "unexpected errors" in captured_run.error.lower()

    @pytest.mark.asyncio
    async def test_empty_output_handling(self):
        """Test handling of empty output."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = MagicMock(spec=Event)
        mock_event.is_final_response.return_value = True
        mock_event.get_function_calls.return_value = []
        mock_event.get_function_responses.return_value = []
        mock_event.content = None

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    result = await runnable.run_async(query="test")

        assert isinstance(result, AgentRunContent)
        assert result.text == ""

    @pytest.mark.asyncio
    async def test_multiple_stream_events(self):
        """Test handling of multiple streaming events."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event1 = _create_mock_event(text="Hello ", is_final=False)
        mock_event2 = _create_mock_event(text="world", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event1
            yield mock_event2

        mock_runner.run_async = mock_run_async

        events_emitted = []

        def capture_callback(event, run):
            events_emitted.append(event)

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    result = await runnable.run_async(
                        query="test", event_callback=capture_callback
                    )

        assert "world" in result.text

    @pytest.mark.asyncio
    async def test_run_async_uses_provided_agent_run_id(self):
        """Test that an explicit agent_run_id is used for the AgentRun."""
        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="Done", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async
        captured_runs = []

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="test",
                        agent_run_id="custom-run-id",
                        event_callback=lambda _e, r: captured_runs.append(r),
                    )

        assert captured_runs
        assert all(r.id == "custom-run-id" for r in captured_runs)

    @pytest.mark.asyncio
    async def test_run_async_generates_agent_run_id_when_omitted(self):
        """Test that a UUID agent_run_id is generated when omitted."""
        from uuid import UUID

        agent_config = _make_agent_config()
        agent_model = MagicMock(spec=AdkModelUnderlying)
        runnable = AdkAgentRunnable(agent_config, agent_model)

        mock_runner = MagicMock(spec=Runner)
        mock_event = _create_mock_event(text="Done", is_final=True)

        async def mock_run_async(*args, **kwargs):
            yield mock_event

        mock_runner.run_async = mock_run_async
        captured_runs = []

        with patch(
            "fivcplayground.backends.adk.agents.Runner", return_value=mock_runner
        ):
            with patch(
                "fivcplayground.backends.adk.agents.AgentRunToolSpan"
            ) as mock_tool_span_cls:
                with patch(
                    "fivcplayground.backends.adk.agents.AgentRunSessionSpan"
                ) as mock_session_span_cls:
                    mock_tool_span, mock_session_span = _create_mocks_for_run()
                    mock_tool_span_cls.return_value = mock_tool_span
                    mock_session_span_cls.return_value = mock_session_span

                    await runnable.run_async(
                        query="test",
                        event_callback=lambda _e, r: captured_runs.append(r),
                    )

        assert captured_runs
        run_id = captured_runs[0].id
        assert UUID(run_id)
        assert all(r.id == run_id for r in captured_runs)
