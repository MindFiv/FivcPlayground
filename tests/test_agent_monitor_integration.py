"""
Integration tests for AgentsMonitor with Chat.

Tests the integration of AgentsMonitor with Chat and real agent execution:
- Chat uses AgentsMonitorManager correctly
- Monitor integration with agent execution
- UI callback flow with unified on_event callback
- Multiple executions with cleanup
- Async execution compatibility
"""

import pytest
import dotenv
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import AIMessage
from fivcplayground.app.utils.chats import Chat
from fivcplayground.agents.types import AgentsMonitor, AgentsRuntime
from fivcplayground import tools

dotenv.load_dotenv()


@pytest.fixture
def mock_tools_retriever():
    """Create a mock tools retriever."""
    retriever = Mock(spec=tools.ToolsRetriever)
    retriever.retrieve.return_value = []
    # Mock to_tool() to return a valid tool spec
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    retriever.to_tool.return_value = mock_tool
    return retriever


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    from fivcplayground.agents.types.repositories import AgentsRuntimeRepository

    repo = Mock(spec=AgentsRuntimeRepository)
    repo.list_agent_runtimes.return_value = []
    repo.get_agent_runtime.return_value = None
    repo.update_agent.return_value = None
    repo.update_agent_runtime.return_value = None
    return repo


class TestChatMonitorIntegration:
    """Test Chat integration with AgentsMonitor."""

    def test_chat_creates_monitor_manager(self, mock_tools_retriever):
        """Test that Chat creates an AgentsMonitorManager instance."""
        manager = Chat(tools_retriever=mock_tools_retriever)

        assert hasattr(manager, "monitor_manager")
        from fivcplayground.agents.types import AgentsMonitorManager

        assert isinstance(manager.monitor_manager, AgentsMonitorManager)

    @pytest.mark.asyncio
    async def test_multiple_executions(self, mock_tools_retriever, mock_repo):
        """Test that monitor works correctly across multiple executions."""
        manager = Chat(
            agent_runtime_repo=mock_repo, tools_retriever=mock_tools_retriever
        )

        # Mock the agent creation and execution
        mock_agent = Mock()
        mock_agent.agent_id = "test-agent-id"
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.run_async = AsyncMock(
            return_value=Mock(output="Test response", message={})
        )

        with patch.object(
            manager.monitor_manager, "create_agent_runtime", return_value=mock_agent
        ):
            # Mock create_briefing_task to avoid actual agent creation
            with patch(
                "fivcplayground.app.utils.chats.create_briefing_task"
            ) as mock_briefing_task, patch(
                "fivcplayground.app.utils.chats.agents.default_retriever.get"
            ) as mock_agent_creator_getter:
                # Mock the task to return a mock with run_async method that returns BaseMessage
                mock_task = Mock()
                mock_desc_msg = AIMessage(content="Agent description")
                mock_task.run_async = AsyncMock(return_value=mock_desc_msg)
                mock_briefing_task.return_value = mock_task

                # Mock the agent creator function
                mock_agent_creator = Mock(return_value=mock_agent)
                mock_agent_creator_getter.return_value = mock_agent_creator

                # First execution - should call briefing task to create agent metadata
                await manager.ask_async("query 1")
                assert mock_briefing_task.call_count == 1

                # Second execution - should NOT call briefing task (metadata already exists)
                await manager.ask_async("query 2")
                assert mock_briefing_task.call_count == 1  # Still 1, not 2


class TestMonitorWithMockAgent:
    """Test monitor with simulated agent events."""

    @pytest.mark.asyncio
    async def test_monitor_captures_streaming_events(
        self, mock_tools_retriever, mock_repo
    ):
        """Test that monitor captures streaming events during execution."""
        from fivcplayground.agents.types.base import AgentsEvent

        _ = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_tools_retriever)

        captured_runtimes = []

        def on_event(runtime: AgentsRuntime):
            # Capture runtime state
            captured_runtimes.append(
                {
                    "streaming_text": runtime.streaming_text,
                    "tool_calls": len(runtime.tool_calls),
                }
            )

        # Create a real monitor with the callback
        monitor = AgentsMonitor(on_event=on_event, runtime_repo=mock_repo)

        # Simulate streaming events through the monitor
        runtime = monitor._runtime

        # Simulate start event
        monitor(AgentsEvent.START, runtime)

        # Simulate streaming messages
        runtime.streaming_text = "Hello"
        monitor(AgentsEvent.UPDATE, runtime)

        runtime.streaming_text = "Hello world"
        monitor(AgentsEvent.UPDATE, runtime)

        # Simulate finish event
        monitor(AgentsEvent.FINISH, runtime)

        # Verify streaming was captured
        assert len(captured_runtimes) >= 2
        # Check that streaming text was accumulated
        assert any(
            "Hello" in str(rt.get("streaming_text", "")) for rt in captured_runtimes
        )

    @pytest.mark.asyncio
    async def test_monitor_captures_tool_events(self, mock_tools_retriever, mock_repo):
        """Test that monitor captures tool events during execution."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        captured_runtimes = []

        def on_event(runtime: AgentsRuntime):
            # Capture runtime state
            captured_runtimes.append(
                {
                    "tool_call_count": len(runtime.tool_calls),
                    "tool_calls": list(runtime.tool_calls.keys()),
                }
            )

        # Create a real monitor with the callback
        monitor = AgentsMonitor(on_event=on_event, runtime_repo=mock_repo)

        # Simulate tool events through the monitor
        runtime = monitor._runtime

        # Simulate start event
        monitor(AgentsEvent.START, runtime)

        # Simulate tool call
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call
        monitor(AgentsEvent.UPDATE, runtime)

        # Simulate finish event
        runtime.reply = "The answer is 4"
        monitor(AgentsEvent.FINISH, runtime)

        # Verify tool events were captured
        assert len(captured_runtimes) >= 2
        # Check that tool calls were captured
        assert any(rt.get("tool_call_count", 0) > 0 for rt in captured_runtimes)

    @pytest.mark.asyncio
    async def test_monitor_with_both_streaming_and_tools(
        self, mock_tools_retriever, mock_repo
    ):
        """Test monitor handling both streaming and tool events."""
        from fivcplayground.agents.types.base import AgentsEvent, AgentsRuntimeToolCall

        captured_runtimes = []

        def on_event(runtime: AgentsRuntime):
            # Capture complete runtime state
            captured_runtimes.append(
                {
                    "streaming_text": runtime.streaming_text,
                    "tool_call_count": len(runtime.tool_calls),
                }
            )

        monitor = AgentsMonitor(on_event=on_event, runtime_repo=mock_repo)

        # Simulate both streaming and tool events through the monitor
        runtime = monitor._runtime

        # Simulate start event
        monitor(AgentsEvent.START, runtime)

        # Simulate streaming text
        runtime.streaming_text = "Let me calculate that. "
        monitor(AgentsEvent.UPDATE, runtime)

        # Simulate tool call
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="123",
            tool_name="calculator",
            tool_input={},
        )
        runtime.tool_calls["123"] = tool_call
        monitor(AgentsEvent.UPDATE, runtime)

        # Simulate more streaming text
        runtime.streaming_text = "Let me calculate that. The answer is 42."
        monitor(AgentsEvent.UPDATE, runtime)

        # Simulate finish event
        runtime.reply = "Let me calculate that. The answer is 42."
        monitor(AgentsEvent.FINISH, runtime)

        # Verify both types of events were captured
        assert len(captured_runtimes) >= 3
        # Check that we have streaming text and tool calls
        assert any(rt.get("streaming_text") for rt in captured_runtimes)
        assert any(rt.get("tool_call_count", 0) > 0 for rt in captured_runtimes)

        # Last streaming event should have full text
        assert (
            captured_runtimes[-2]["streaming_text"]
            == "Let me calculate that. The answer is 42."
        )


class TestMonitorErrorHandling:
    """Test monitor error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_callback_exception_doesnt_break_execution(
        self, mock_tools_retriever, mock_repo
    ):
        """Test that callback exceptions don't break agent execution."""
        manager = Chat(
            agent_runtime_repo=mock_repo, tools_retriever=mock_tools_retriever
        )

        def failing_callback(runtime):
            raise ValueError("Callback error")

        # Mock agent
        mock_agent = Mock()
        mock_agent.agent_id = "test-agent-id"
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"

        async def mock_invoke(query):
            # Even with failing callback, execution should continue
            return Mock(output="test", message={})

        mock_agent.run_async = mock_invoke

        with patch.object(
            manager.monitor_manager, "create_agent_runtime", return_value=mock_agent
        ):
            # Mock create_briefing_task to avoid actual agent creation
            with patch(
                "fivcplayground.app.utils.chats.create_briefing_task"
            ) as mock_briefing_task, patch(
                "fivcplayground.app.utils.chats.agents.default_retriever.get"
            ) as mock_agent_creator_getter:
                # Mock the task to return a mock with run_async method that returns BaseMessage
                mock_task = Mock()
                mock_desc_msg = AIMessage(content="Agent description")
                mock_task.run_async = AsyncMock(return_value=mock_desc_msg)
                mock_briefing_task.return_value = mock_task

                # Mock the agent creator function
                mock_agent_creator = Mock(return_value=mock_agent)
                mock_agent_creator_getter.return_value = mock_agent_creator

                # Should not raise exception despite failing callback
                result = await manager.ask_async("test", on_event=failing_callback)

                # Execution should complete successfully
                assert result is not None


class TestMonitorStateManagement:
    """Test monitor state management across executions."""

    @pytest.mark.asyncio
    async def test_state_isolated_between_runs(self, mock_tools_retriever, mock_repo):
        """Test that state is properly isolated between runs."""
        from fivcplayground.agents.types.base import AgentsEvent

        captured_first = []
        captured_second = []

        def on_event_first(runtime: AgentsRuntime):
            captured_first.append(runtime.streaming_text)

        def on_event_second(runtime: AgentsRuntime):
            captured_second.append(runtime.streaming_text)

        monitor_1 = AgentsMonitor(on_event=on_event_first, runtime_repo=mock_repo)
        monitor_2 = AgentsMonitor(on_event=on_event_second, runtime_repo=mock_repo)

        # Simulate events for first monitor
        runtime_1 = monitor_1._runtime
        monitor_1(AgentsEvent.START, runtime_1)

        runtime_1.streaming_text = "First response"
        monitor_1(AgentsEvent.UPDATE, runtime_1)

        monitor_1(AgentsEvent.FINISH, runtime_1)

        # Simulate events for second monitor
        runtime_2 = monitor_2._runtime
        monitor_2(AgentsEvent.START, runtime_2)

        runtime_2.streaming_text = "Second response"
        monitor_2(AgentsEvent.UPDATE, runtime_2)

        monitor_2(AgentsEvent.FINISH, runtime_2)

        # State should be isolated between runs
        assert len(captured_first) > 0
        assert len(captured_second) > 0
        assert "First" in captured_first[-1]
        assert "Second" in captured_second[-1]
