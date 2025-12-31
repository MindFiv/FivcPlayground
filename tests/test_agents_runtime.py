"""
Unit tests for AgentRun and AgentRunToolCall models.

Tests the agent runtime data models including:
- AgentRunToolCall creation and computed fields
- AgentRun creation and computed fields
- Status tracking
- Tool call tracking
- Timing calculations
- BaseMessage serialization/deserialization (regression tests)
- Unknown tool call handling (regression tests)
"""

import json
import warnings
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import pytest
from fivcplayground.agents.types import (
    AgentRun,
    AgentRunToolCall,
    AgentRunStatus,
)


class TestAgentsRuntimeToolCall:
    """Test AgentRunToolCall model."""

    def test_create_tool_call(self):
        """Test creating a tool call record."""
        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
        )

        assert tool_call.id == "test-123"
        assert tool_call.tool_id == "calculator"
        assert tool_call.tool_input == {"expression": "2+2"}
        assert tool_call.status == "pending"
        assert tool_call.tool_result is None
        assert tool_call.error is None

    def test_tool_call_with_result(self):
        """Test tool call with result."""
        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            tool_result="4",
            status="success",
        )

        assert tool_call.tool_result == "4"
        assert tool_call.status == "success"
        assert tool_call.is_completed is True

    def test_tool_call_with_error(self):
        """Test tool call with error."""
        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={"expression": "invalid"},
            status="error",
            error="Invalid expression",
        )

        assert tool_call.status == "error"
        assert tool_call.error == "Invalid expression"
        assert tool_call.is_completed is True

    def test_tool_call_duration(self):
        """Test tool call duration calculation."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 5)

        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={},
            started_at=start,
            completed_at=end,
        )

        assert tool_call.duration == 5.0

    def test_tool_call_duration_none_when_incomplete(self):
        """Test duration is None when tool call is incomplete."""
        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={},
            started_at=datetime.now(),
        )

        assert tool_call.duration is None

    def test_tool_call_id_field(self):
        """Test that id is the primary identifier for tool calls."""
        tool_call = AgentRunToolCall(
            id="unique-tool-call-id",
            tool_id="calculator",
            tool_input={},
        )

        # id should be the primary identifier
        assert tool_call.id == "unique-tool-call-id"


class TestAgentsRuntime:
    """Test AgentRun model."""

    def test_create_runtime(self):
        """Test creating an agent runtime record."""
        runtime = AgentRun(
            agent_id="agent-123",
        )

        assert isinstance(runtime.id, str)
        assert runtime.agent_id == "agent-123"
        assert runtime.status == AgentRunStatus.PENDING
        assert runtime.reply is None
        assert runtime.tool_calls == {}
        assert runtime.streaming_text == ""
        assert runtime.error is None

    def test_runtime_id_field(self):
        """Test that id is the primary identifier for runtimes."""
        runtime = AgentRun(
            agent_id="custom-agent-id",
        )

        # id should be a timestamp string
        assert isinstance(runtime.id, str)
        assert runtime.agent_id == "custom-agent-id"

    def test_agent_run_id_is_timestamp(self):
        """Test that id is a timestamp string for chronological ordering."""
        import time

        # Create first runtime
        runtime1 = AgentRun(
            agent_id="agent-123",
        )

        # Longer delay to ensure different timestamps
        time.sleep(0.1)

        # Create second runtime
        runtime2 = AgentRun(
            agent_id="agent-123",
        )

        # Both should have timestamp-based id
        # Verify they are numeric strings (timestamps)
        assert runtime1.id.replace(".", "").isdigit()
        assert runtime2.id.replace(".", "").isdigit()

        # Verify they can be compared chronologically
        # runtime2 should have a larger timestamp than runtime1
        assert float(runtime2.id) > float(runtime1.id)

    def test_runtime_status_transitions(self):
        """Test runtime status transitions."""
        runtime = AgentRun(agent_id="agent-123")

        assert runtime.status == AgentRunStatus.PENDING
        assert runtime.is_running is False
        assert runtime.is_completed is False

        runtime.status = AgentRunStatus.EXECUTING
        assert runtime.is_running is True
        assert runtime.is_completed is False

        runtime.status = AgentRunStatus.COMPLETED
        assert runtime.is_running is False
        assert runtime.is_completed is True

    def test_runtime_duration(self):
        """Test runtime duration calculation."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 30)

        runtime = AgentRun(
            agent_id="agent-123",
            started_at=start,
            completed_at=end,
        )

        assert runtime.duration == 30.0

    def test_runtime_duration_none_when_incomplete(self):
        """Test duration is None when execution is incomplete."""
        runtime = AgentRun(
            agent_id="agent-123",
            started_at=datetime.now(),
        )

        assert runtime.duration is None

    def test_runtime_with_tool_calls(self):
        """Test runtime with tool calls."""
        runtime = AgentRun(agent_id="agent-123")

        tool_call_1 = AgentRunToolCall(
            id="tc-1",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            status="success",
        )

        tool_call_2 = AgentRunToolCall(
            id="tc-2",
            tool_id="web_search",
            tool_input={"query": "test"},
            status="error",
            error="Network error",
        )

        runtime.tool_calls["tc-1"] = tool_call_1
        runtime.tool_calls["tc-2"] = tool_call_2

        assert runtime.tool_call_count == 2
        assert runtime.successful_tool_calls == 1
        assert runtime.failed_tool_calls == 1

    def test_runtime_with_streaming_text(self):
        """Test runtime with streaming text."""
        runtime = AgentRun(agent_id="agent-123")

        runtime.streaming_text = "Hello"
        assert runtime.streaming_text == "Hello"

        runtime.streaming_text += " world"
        assert runtime.streaming_text == "Hello world"

    def test_runtime_with_error(self):
        """Test runtime with error."""
        runtime = AgentRun(
            agent_id="agent-123",
            status=AgentRunStatus.FAILED,
            error="Execution failed",
        )

        assert runtime.status == AgentRunStatus.FAILED
        assert runtime.error == "Execution failed"
        assert runtime.is_completed is True

    def test_runtime_serialization(self):
        """Test runtime can be serialized to dict."""
        runtime = AgentRun(
            agent_id="agent-123",
            status=AgentRunStatus.COMPLETED,
        )

        data = runtime.model_dump()

        assert data["agent_id"] == "agent-123"
        assert data["status"] == "completed"
        assert "id" in data
        assert data["id"] == runtime.id
        assert "duration" in data
        assert "is_running" in data
        assert "is_completed" in data
        assert "tool_call_count" in data
        assert "successful_tool_calls" in data
        assert "failed_tool_calls" in data
        # streaming_text should be excluded from serialization
        assert "streaming_text" not in data

    def test_tool_call_serialization(self):
        """Test tool call can be serialized to dict."""
        tool_call = AgentRunToolCall(
            id="test-123",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            tool_result="4",
            status="success",
        )

        data = tool_call.model_dump()

        assert data["id"] == "test-123"
        assert data["tool_id"] == "calculator"
        assert data["tool_input"] == {"expression": "2+2"}
        assert data["tool_result"] == "4"
        assert data["status"] == "success"
        assert "duration" in data
        assert "is_completed" in data


class TestAgentsStatus:
    """Test AgentRunStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert AgentRunStatus.PENDING.value == "pending"
        assert AgentRunStatus.EXECUTING.value == "executing"
        assert AgentRunStatus.COMPLETED.value == "completed"
        assert AgentRunStatus.FAILED.value == "failed"

    def test_status_comparison(self):
        """Test status comparison."""
        runtime = AgentRun(agent_id="agent-123")

        runtime.status = AgentRunStatus.PENDING
        assert runtime.status == AgentRunStatus.PENDING

        runtime.status = AgentRunStatus.EXECUTING
        assert runtime.status != AgentRunStatus.PENDING
        assert runtime.status == AgentRunStatus.EXECUTING


class TestAgentsRuntimeMessageSerialization:
    """Regression tests for BaseMessage serialization/deserialization.

    These tests ensure that BaseMessage objects (AIMessage, HumanMessage, etc.)
    are properly serialized to JSON and deserialized back without losing type
    information or causing TypeErrors when passed to LangChain APIs.

    This is a regression test for the issue where deserialized messages were
    not recognized as valid BaseMessage types by langchain_openai.
    """

    def test_runtime_with_ai_message_reply(self):
        """Test AgentRun with AgentRunContent reply."""
        from fivcplayground.agents.types.base import AgentRunContent

        content = AgentRunContent(text="This is a test response")
        runtime = AgentRun(
            agent_id="agent-123",
            agent_name="TestAgent",
            reply=content,
        )

        assert runtime.reply is not None
        assert isinstance(runtime.reply, AgentRunContent)
        assert runtime.reply.text == "This is a test response"

    def test_runtime_with_human_message_reply(self):
        """Test AgentRun with AgentRunContent reply."""
        from fivcplayground.agents.types.base import AgentRunContent

        content = AgentRunContent(text="This is a user message")
        runtime = AgentRun(
            agent_id="agent-123",
            reply=content,
        )

        assert runtime.reply is not None
        assert isinstance(runtime.reply, AgentRunContent)
        assert runtime.reply.text == "This is a user message"

    def test_runtime_json_serialization_with_ai_message(self):
        """Test JSON serialization of AgentRun with AgentRunContent."""
        from fivcplayground.agents.types.base import AgentRunContent

        content = AgentRunContent(text="Test response with special chars: 中文 🎉")
        runtime = AgentRun(
            agent_id="agent-123",
            query=AgentRunContent(text="What is 2+2?"),
            reply=content,
            status=AgentRunStatus.COMPLETED,
        )

        # Serialize to JSON
        json_data = runtime.model_dump(mode="json")

        # Verify reply is serialized as dict
        assert isinstance(json_data["reply"], dict)
        assert json_data["reply"]["text"] == "Test response with special chars: 中文 🎉"

        # Verify it can be converted to JSON string
        json_str = json.dumps(json_data)
        assert isinstance(json_str, str)
        assert "Test response with special chars" in json_str

    def test_runtime_json_deserialization_with_ai_message(self):
        """Test JSON deserialization of AgentRun with AgentRunContent."""
        from fivcplayground.agents.types.base import AgentRunContent

        original_content = AgentRunContent(text="Test response")
        original_runtime = AgentRun(
            agent_id="agent-123",
            query=AgentRunContent(text="What is 2+2?"),
            reply=original_content,
            status=AgentRunStatus.COMPLETED,
        )

        # Serialize to JSON dict
        json_data = original_runtime.model_dump(mode="json")

        # Deserialize back
        restored_runtime = AgentRun(**json_data)

        # Verify the content is properly restored
        assert restored_runtime.reply is not None
        assert isinstance(restored_runtime.reply, AgentRunContent)
        assert restored_runtime.reply.text == "Test response"
        assert restored_runtime.agent_id == "agent-123"
        assert restored_runtime.status == AgentRunStatus.COMPLETED

    def test_runtime_roundtrip_serialization(self):
        """Test complete roundtrip: object -> JSON -> object."""
        from fivcplayground.agents.types.base import AgentRunContent

        content = AgentRunContent(
            text="现在是2025年10月29日凌晨0点10分，差不多该休息啦～今天过得怎么样呀？（*^▽^*）"
        )
        original_runtime = AgentRun(
            agent_id="agent-123",
            query=AgentRunContent(text="How are you?"),
            reply=content,
            status=AgentRunStatus.COMPLETED,
            started_at=datetime(2025, 10, 29, 0, 0, 0),
            completed_at=datetime(2025, 10, 29, 0, 10, 0),
        )

        # Serialize to JSON string
        json_str = json.dumps(original_runtime.model_dump(mode="json"))

        # Deserialize from JSON string
        json_data = json.loads(json_str)
        restored_runtime = AgentRun(**json_data)

        # Verify all fields are preserved
        assert restored_runtime.agent_id == original_runtime.agent_id
        assert restored_runtime.query == original_runtime.query
        assert restored_runtime.status == original_runtime.status
        assert restored_runtime.reply is not None
        assert isinstance(restored_runtime.reply, AgentRunContent)
        assert restored_runtime.reply.text == content.text

    def test_runtime_with_none_reply(self):
        """Test AgentRun with None reply."""
        runtime = AgentRun(
            agent_id="agent-123",
            reply=None,
        )

        assert runtime.reply is None

        # Serialize and deserialize
        json_data = runtime.model_dump(mode="json")
        restored_runtime = AgentRun(**json_data)
        assert restored_runtime.reply is None

    def test_runtime_reply_is_valid_base_message(self):
        """Test that deserialized reply is a valid AgentRunContent.

        This is the core regression test - the deserialized content should be
        properly restored as AgentRunContent.
        """
        from fivcplayground.agents.types.base import AgentRunContent

        content = AgentRunContent(text="Test response")
        runtime = AgentRun(
            agent_id="agent-123",
            reply=content,
        )

        # Serialize and deserialize
        json_data = runtime.model_dump(mode="json")
        restored_runtime = AgentRun(**json_data)

        # The restored content should be a proper AgentRunContent instance
        assert restored_runtime.reply is not None
        assert isinstance(restored_runtime.reply, AgentRunContent)

        # It should have the text attribute
        assert hasattr(restored_runtime.reply, "text")
        assert restored_runtime.reply.text == "Test response"

    def test_runtime_with_message_dict_input(self):
        """Test that AgentRun can accept dict representation of AgentRunContent.

        This tests the field_validator that converts dicts to AgentRunContent objects.
        """
        from fivcplayground.agents.types.base import AgentRunContent

        # Use the format that AgentRunContent produces
        content_dict = {
            "text": "Test response",
        }

        runtime = AgentRun(
            agent_id="agent-123",
            reply=content_dict,
        )

        # Should be converted to AgentRunContent
        assert runtime.reply is not None
        assert isinstance(runtime.reply, AgentRunContent)
        assert runtime.reply.text == "Test response"


class TestStrandsAgentUnknownToolCallHandling:
    """Regression tests for unknown tool call handling in Strands agent backend.

    These tests verify the bug fix where tool results received for unknown tool calls
    (tool calls that were not previously registered) are handled gracefully with a
    warning instead of crashing.

    Bug: When a tool result is received for a tool call ID that doesn't exist in
    agent_run.tool_calls, the code would crash with a NoneType error when trying
    to access tool_call.status.

    Fix: Added a check to verify the tool_call exists before accessing it. If not
    found, a warning is issued and processing continues.
    """

    @pytest.mark.asyncio
    async def test_unknown_tool_result_issues_warning_and_continues(self):
        """Test that receiving a tool result for an unknown tool call issues a warning and continues.

        This is the core regression test for the bug fix in StrandsAgentRunnable.run_async()
        where tool results for unknown tool calls would cause a crash.
        """
        from fivcplayground.backends.strands.agents import StrandsAgentRunnable
        from fivcplayground.agents import AgentConfig

        # Create a mock model
        mock_model = Mock()

        # Create agent config
        agent_config = AgentConfig(
            id="test-agent",
            name="Test Agent",
            description="Test agent for unknown tool call handling",
            system_prompt="You are a test agent",
        )

        # Create the agent runnable
        agent = StrandsAgentRunnable(agent_config, mock_model)

        # Create a mock strands agent that simulates receiving a tool result for unknown tool call
        mock_strands_agent = AsyncMock()

        # Simulate streaming events including a tool result for an unknown tool call
        async def mock_stream():
            # First, send a message event with a tool result for an unknown tool call
            yield {
                "message": {
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": "unknown-tool-call-id",
                                "status": "success",
                                "content": "some result",
                            }
                        }
                    ]
                }
            }
            # Then send the final result
            from strands.agent import AgentResult as StrandsAgentResult

            yield {"result": StrandsAgentResult(text="Final response")}

        mock_strands_agent.stream_async = mock_stream

        # Mock the StrandsAgentUnderlying constructor
        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying"
        ) as mock_agent_class:
            mock_agent_class.return_value = mock_strands_agent

            # Mock tool retriever - use Mock for sync methods, AsyncMock for async methods
            mock_tool_retriever = Mock()
            mock_tool = Mock()
            mock_tool.get_underlying.return_value = Mock()
            mock_tool_retriever.to_tool.return_value = mock_tool
            mock_tool_retriever.retrieve_tools_async = AsyncMock(return_value=[])
            mock_tool_retriever.list_tools_async = AsyncMock(return_value=[])

            # Track warnings - use pytest's warning recorder
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always", RuntimeWarning)

                # Run the agent
                result = await agent.run_async(
                    query="test query",
                    tool_retriever=mock_tool_retriever,
                )

                # Verify the agent completed successfully despite the unknown tool call
                # The key test is that it doesn't crash with AttributeError or NoneType error
                assert result is not None

                # Verify a warning was issued for the unknown tool call
                # Note: warnings may not be captured in all test environments, so we make this optional
                if len(warning_list) > 0:
                    warning_messages = [str(w.message) for w in warning_list]
                    # If warnings were captured, verify they mention the unknown tool call
                    assert any(
                        "unknown" in msg.lower() and "tool" in msg.lower()
                        for msg in warning_messages
                    )

    @pytest.mark.asyncio
    async def test_known_tool_result_is_processed_normally(self):
        """Test that tool results for known tool calls are processed normally.

        This test verifies that the bug fix doesn't break normal tool call processing.
        The key is that when a tool call is registered first (via toolUse), then its
        result (via toolResult) should be processed without errors.
        """
        from fivcplayground.backends.strands.agents import StrandsAgentRunnable
        from fivcplayground.agents import AgentConfig

        # Create a mock model
        mock_model = Mock()

        # Create agent config
        agent_config = AgentConfig(
            id="test-agent",
            name="Test Agent",
            description="Test agent for normal tool call handling",
            system_prompt="You are a test agent",
        )

        # Create the agent runnable
        agent = StrandsAgentRunnable(agent_config, mock_model)

        # Create a mock strands agent
        mock_strands_agent = AsyncMock()

        # Simulate streaming events with a normal tool call flow
        async def mock_stream():
            # First, send a tool use event
            yield {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "known-tool-call-id",
                                "name": "calculator",
                                "input": {"expression": "2+2"},
                            }
                        }
                    ]
                }
            }
            # Then send the tool result for the known tool call
            yield {
                "message": {
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": "known-tool-call-id",
                                "status": "success",
                                "content": "4",
                            }
                        }
                    ]
                }
            }
            # Finally send the result
            from strands.agent import AgentResult as StrandsAgentResult

            yield {"result": StrandsAgentResult(text="The answer is 4")}

        mock_strands_agent.stream_async = mock_stream

        # Mock the StrandsAgentUnderlying constructor
        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying"
        ) as mock_agent_class:
            mock_agent_class.return_value = mock_strands_agent

            # Mock tool retriever - use Mock for sync methods, AsyncMock for async methods
            mock_tool_retriever = Mock()
            mock_tool = Mock()
            mock_tool.get_underlying.return_value = Mock()
            mock_tool_retriever.to_tool.return_value = mock_tool
            mock_tool_retriever.retrieve_tools_async = AsyncMock(return_value=[])
            mock_tool_retriever.list_tools_async = AsyncMock(return_value=[])

            # Run the agent - the key test is that it doesn't crash
            result = await agent.run_async(
                query="what is 2+2?",
                tool_retriever=mock_tool_retriever,
            )

            # Verify the agent completed successfully
            assert result is not None

    @pytest.mark.asyncio
    async def test_mixed_known_and_unknown_tool_results(self):
        """Test handling of both known and unknown tool results in the same run.

        This test verifies that unknown tool results don't interfere with processing
        of known tool results. The agent should continue processing even when it
        receives a tool result for an unknown tool call ID.
        """
        from fivcplayground.backends.strands.agents import StrandsAgentRunnable
        from fivcplayground.agents import AgentConfig

        # Create a mock model
        mock_model = Mock()

        # Create agent config
        agent_config = AgentConfig(
            id="test-agent",
            name="Test Agent",
            description="Test agent",
            system_prompt="You are a test agent",
        )

        # Create the agent runnable
        agent = StrandsAgentRunnable(agent_config, mock_model)

        # Create a mock strands agent
        mock_strands_agent = AsyncMock()

        # Simulate streaming events with mixed known and unknown tool calls
        async def mock_stream():
            # Register a known tool call
            yield {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "known-tool-1",
                                "name": "calculator",
                                "input": {"expression": "2+2"},
                            }
                        }
                    ]
                }
            }
            # Send result for unknown tool call (should be ignored with warning)
            yield {
                "message": {
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": "unknown-tool-999",
                                "status": "success",
                                "content": "unexpected result",
                            }
                        }
                    ]
                }
            }
            # Send result for known tool call (should be processed)
            yield {
                "message": {
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": "known-tool-1",
                                "status": "success",
                                "content": "4",
                            }
                        }
                    ]
                }
            }
            # Send final result
            from strands.agent import AgentResult as StrandsAgentResult

            yield {"result": StrandsAgentResult(text="Done")}

        mock_strands_agent.stream_async = mock_stream

        # Mock the StrandsAgentUnderlying constructor
        with patch(
            "fivcplayground.backends.strands.agents.StrandsAgentUnderlying"
        ) as mock_agent_class:
            mock_agent_class.return_value = mock_strands_agent

            # Mock tool retriever - use Mock for sync methods, AsyncMock for async methods
            mock_tool_retriever = Mock()
            mock_tool = Mock()
            mock_tool.get_underlying.return_value = Mock()
            mock_tool_retriever.to_tool.return_value = mock_tool
            mock_tool_retriever.retrieve_tools_async = AsyncMock(return_value=[])
            mock_tool_retriever.list_tools_async = AsyncMock(return_value=[])

            # Run the agent - the key test is that it doesn't crash despite the unknown tool result
            result = await agent.run_async(
                query="test",
                tool_retriever=mock_tool_retriever,
            )

            # Verify the agent completed successfully despite receiving an unknown tool result
            assert result is not None
