"""
Unit tests for AgentsMonitor class.

Tests the agent execution monitoring functionality including:
- Initialization with and without callbacks
- Streaming event parsing and accumulation
- Tool event capture (toolUse and toolResult)
- Callback invocation with AgentsRuntime
- Error handling
- State access via tool_calls property
- Cleanup functionality
"""

from unittest.mock import Mock
from fivcplayground.agents.types import AgentsMonitor, AgentsRuntime


class TestAgentsMonitorInitialization:
    """Test AgentsMonitor initialization."""

    def test_init_without_callbacks(self):
        """Test creating monitor without callbacks."""
        monitor = AgentsMonitor()

        assert monitor._on_event is None
        assert monitor._runtime is not None
        assert isinstance(monitor._runtime, AgentsRuntime)
        assert monitor._runtime.streaming_text == ""
        assert monitor.tool_calls == []

    def test_init_with_callback(self):
        """Test creating monitor with event callback."""
        on_event = Mock()

        monitor = AgentsMonitor(on_event=on_event)

        assert monitor._on_event is on_event
        assert monitor._runtime is not None

    def test_init_with_custom_runtime(self):
        """Test creating monitor with custom runtime."""
        custom_runtime = AgentsRuntime(agent_id="test-agent", streaming_text="initial")
        monitor = AgentsMonitor(runtime=custom_runtime)

        assert monitor._runtime is custom_runtime
        assert monitor._runtime.agent_id == "test-agent"
        assert monitor._runtime.streaming_text == "initial"


class TestAgentsMonitorStreaming:
    """Test streaming message tracking."""

    def test_handle_stream_event_single_chunk(self):
        """Test handling a single streaming chunk with UPDATE event."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Simulate streaming text accumulation
        runtime.streaming_text = "Hello"

        # Call monitor with UPDATE event
        monitor(AgentsEvent.UPDATE, runtime)

        assert monitor._runtime.streaming_text == "Hello"

    def test_handle_stream_event_multiple_chunks(self):
        """Test accumulating multiple streaming chunks."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        chunks = ["Hello", " ", "world", "!"]
        for chunk in chunks:
            runtime.streaming_text += chunk
            monitor(AgentsEvent.UPDATE, runtime)

        assert monitor._runtime.streaming_text == "Hello world!"

    def test_stream_callback_invoked_with_runtime(self):
        """Test that on_event callback is invoked with runtime after streaming."""
        from fivcplayground.agents.types.base import AgentsEvent

        on_event = Mock()
        monitor = AgentsMonitor(on_event=on_event)
        runtime = monitor._runtime

        runtime.streaming_text = "test"
        monitor(AgentsEvent.UPDATE, runtime)

        on_event.assert_called_once()
        # Verify the callback received the runtime
        call_args = on_event.call_args[0][0]
        assert isinstance(call_args, AgentsRuntime)
        assert call_args.streaming_text == "test"

    def test_stream_callback_multiple_invocations(self):
        """Test callback is invoked for each chunk with updated runtime."""
        from fivcplayground.agents.types.base import AgentsEvent

        captured_texts = []

        def on_event(runtime: AgentsRuntime):
            # Capture the streaming text at each invocation
            captured_texts.append(runtime.streaming_text)

        monitor = AgentsMonitor(on_event=on_event)
        runtime = monitor._runtime

        chunks = ["a", "b", "c"]
        for chunk in chunks:
            runtime.streaming_text += chunk
            monitor(AgentsEvent.UPDATE, runtime)

        # Verify callback was invoked 3 times with accumulated text
        assert len(captured_texts) == 3
        assert captured_texts[0] == "a"
        assert captured_texts[1] == "ab"
        assert captured_texts[2] == "abc"

    def test_content_block_start_clears_streaming_text(self):
        """Test that START event initializes fresh runtime."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add some streaming text
        runtime.streaming_text = "old text"
        monitor(AgentsEvent.UPDATE, runtime)
        assert monitor._runtime.streaming_text == "old text"

        # START event should initialize fresh runtime
        new_runtime = AgentsRuntime()
        monitor(AgentsEvent.START, new_runtime)
        assert monitor._runtime.streaming_text == ""

    def test_malformed_stream_event(self):
        """Test handling malformed streaming events."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Valid update
        runtime.streaming_text = "test"
        monitor(AgentsEvent.UPDATE, runtime)
        assert monitor._runtime.streaming_text == "test"


class TestAgentsMonitorToolEvents:
    """Test tool call event tracking."""

    def test_handle_tool_use_event(self):
        """Test capturing tool use events."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add a tool call to the runtime
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={"expression": "2+2"},
        )
        runtime.tool_calls["123"] = tool_call

        monitor(AgentsEvent.UPDATE, runtime)

        # Verify tool call was tracked
        assert len(monitor.tool_calls) == 1
        assert monitor.tool_calls[0].tool_use_id == "123"
        assert isinstance(monitor._runtime, AgentsRuntime)

    def test_handle_tool_result_event(self):
        """Test capturing tool result events."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add tool call
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call

        monitor(AgentsEvent.UPDATE, runtime)

        # Then finish with result
        runtime.reply = "Result: 4"
        monitor(AgentsEvent.FINISH, runtime)

        # Verify runtime was updated
        assert monitor._runtime.reply == "Result: 4"

    def test_handle_tool_result_failure(self):
        """Test capturing failed tool result."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add tool call
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call

        monitor(AgentsEvent.UPDATE, runtime)

        # Finish with error message
        runtime.reply = "Error occurred"
        monitor(AgentsEvent.FINISH, runtime)

        # Verify runtime was updated
        assert monitor._runtime.reply == "Error occurred"

    def test_tool_callback_invoked_with_runtime(self):
        """Test that on_event callback is invoked with runtime."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        on_event = Mock()
        monitor = AgentsMonitor(on_event=on_event)
        runtime = monitor._runtime

        # Add tool call and update
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call

        monitor(AgentsEvent.UPDATE, runtime)

        on_event.assert_called_once()
        # Verify the callback received the runtime
        call_args = on_event.call_args[0][0]
        assert isinstance(call_args, AgentsRuntime)
        assert len(call_args.tool_calls) == 1

    def test_message_with_text_and_tool(self):
        """Test message containing both text and tool events."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add streaming text and tool call
        runtime.streaming_text = "Let me calculate that"
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call

        monitor(AgentsEvent.UPDATE, runtime)

        # Verify message was processed
        assert monitor._runtime.streaming_text == "Let me calculate that"
        assert len(monitor.tool_calls) == 1


class TestAgentsMonitorErrorHandling:
    """Test error handling in callbacks."""

    def test_stream_callback_exception_handled(self):
        """Test that event callback exceptions don't crash monitor during streaming."""
        from fivcplayground.agents.types.base import AgentsEvent

        def failing_callback(runtime):
            raise ValueError("Test error")

        monitor = AgentsMonitor(on_event=failing_callback)
        runtime = monitor._runtime

        runtime.streaming_text = "test"

        # Should not raise exception
        monitor(AgentsEvent.UPDATE, runtime)

        # Message should still be accumulated
        assert monitor._runtime.streaming_text == "test"

    def test_tool_callback_exception_handled(self):
        """Test that event callback exceptions don't crash monitor during finish events."""
        from fivcplayground.agents.types.base import AgentsEvent

        def failing_callback(runtime):
            raise ValueError("Test error")

        monitor = AgentsMonitor(on_event=failing_callback)
        runtime = monitor._runtime

        runtime.reply = "test response"

        # Should not raise exception
        monitor(AgentsEvent.FINISH, runtime)

        # Event should still be captured
        assert monitor._runtime.reply == "test response"


class TestAgentsMonitorStateAccess:
    """Test state access via properties."""

    def test_tool_calls_property(self):
        """Test that tool_calls property returns list of tool calls."""
        monitor = AgentsMonitor()

        # Tool calls are empty by default
        tool_calls = monitor.tool_calls
        assert len(tool_calls) == 0

    def test_runtime_access(self):
        """Test direct access to runtime for streaming text."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        runtime.streaming_text = "test message"
        monitor(AgentsEvent.UPDATE, runtime)

        assert monitor._runtime.streaming_text == "test message"
        assert isinstance(monitor._runtime, AgentsRuntime)


class TestAgentsMonitorCleanup:
    """Test cleanup functionality."""

    def test_cleanup_clears_message(self):
        """Test that cleanup clears accumulated message."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        runtime.streaming_text = "test"
        monitor(AgentsEvent.UPDATE, runtime)
        assert monitor._runtime.streaming_text == "test"

        monitor.cleanup()
        assert monitor._runtime.streaming_text == ""

    def test_cleanup_clears_tool_calls(self):
        """Test that cleanup clears tool events."""
        monitor = AgentsMonitor()

        # Tool calls are empty by default
        assert len(monitor.tool_calls) == 0

        monitor.cleanup()
        assert len(monitor.tool_calls) == 0

    def test_cleanup_clears_callback(self):
        """Test that cleanup clears callback by default."""
        on_event = Mock()

        monitor = AgentsMonitor(on_event=on_event)
        monitor.cleanup()

        assert monitor._on_event is None

    def test_cleanup_with_new_callback(self):
        """Test that cleanup can set a new callback."""
        old_callback = Mock()
        new_callback = Mock()

        monitor = AgentsMonitor(on_event=old_callback)
        monitor.cleanup(on_event=new_callback)

        assert monitor._on_event is new_callback

    def test_cleanup_with_custom_runtime(self):
        """Test that cleanup can use a custom runtime."""
        from fivcplayground.agents.types.base import AgentsEvent

        monitor = AgentsMonitor()
        runtime = monitor._runtime

        # Add some data
        runtime.streaming_text = "test"
        monitor(AgentsEvent.UPDATE, runtime)

        # Cleanup with custom runtime
        custom_runtime = AgentsRuntime(agent_id="new-agent", streaming_text="new")
        monitor.cleanup(runtime=custom_runtime)

        assert monitor._runtime is custom_runtime
        assert monitor._runtime.agent_id == "new-agent"
        assert monitor._runtime.streaming_text == "new"
