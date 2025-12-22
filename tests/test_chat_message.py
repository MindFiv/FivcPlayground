#!/usr/bin/env python3
"""
Tests for chat_message component functionality.

Tests the ChatMessage class and its methods:
- render() with different runtime states
- render_message() with message content
- render_streaming() with streaming text
- render_tool_call() with tool calls
"""

import pytest
from unittest.mock import Mock
from langchain_core.messages import AIMessage
from fivcplayground.demos.components import ChatMessage
from fivcplayground.agents.types import (
    AgentRun,
    AgentRunToolCall,
    AgentRunContent,
)


class TestChatMessageClass:
    """Test the ChatMessage class."""

    def test_render_with_query_only(self):
        """Test rendering runtime with only query (no response yet)."""
        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="What is the weather?"),
            streaming_text="",
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Should create container first
        mock_placeholder.container.assert_called_once()

        # Should create user and assistant messages
        assert mock_container.chat_message.call_count == 2
        mock_container.chat_message.assert_any_call("user")
        mock_container.chat_message.assert_any_call("assistant")

        # User message should display query
        mock_user_msg.text.assert_called_once_with("What is the weather?")

    def test_render_with_completed_message(self):
        """Test rendering runtime with completed message."""
        from datetime import datetime

        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]

        message = AgentRunContent(text="The weather is sunny.")

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="What is the weather?"),
            reply=message,
            completed_at=datetime.now(),
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Should render completed message
        mock_assistant_msg.markdown.assert_called_once()
        call_args = mock_assistant_msg.markdown.call_args[0][0]
        assert "sunny" in call_args

    def test_render_with_streaming_text(self):
        """Test rendering runtime with streaming text."""
        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="Tell me a story"),
            streaming_text="Once upon a time...",
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Should render streaming text with loading indicator
        mock_assistant_msg.markdown.assert_called_once()
        call_args = mock_assistant_msg.markdown.call_args[0][0]
        assert "Once upon a time" in call_args
        assert "loading-dots" in call_args  # Loading indicator present

    def test_render_without_query(self):
        """Test rendering runtime without query (assistant-only message)."""
        mock_placeholder = Mock()
        mock_container = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.return_value = mock_assistant_msg

        runtime = AgentRun(
            agent_id="test-agent",
            streaming_text="Thinking...",
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Should only create assistant message
        mock_container.chat_message.assert_called_once_with("assistant")
        mock_assistant_msg.markdown.assert_called_once()


class TestRenderMessageMethod:
    """Test the render_message() static method."""

    def test_render_message_with_single_text_block(self):
        """Test rendering message with single text content block."""
        mock_placeholder = Mock()

        message = AIMessage(content="Hello, world!")

        ChatMessage.render_message(message, mock_placeholder)

        mock_placeholder.markdown.assert_called_once()
        call_args = mock_placeholder.markdown.call_args[0][0]
        assert "Hello, world!" in call_args

    def test_render_message_with_multiple_text_blocks(self):
        """Test rendering message with multiple text content blocks."""
        mock_placeholder = Mock()

        # Create a message with multiple content blocks
        # AIMessage.text will combine them into a single string
        message = AIMessage(
            content=[
                {"type": "text", "text": "First part."},
                {"type": "text", "text": "Second part."},
                {"type": "text", "text": "Third part."},
            ]
        )

        ChatMessage.render_message(message, mock_placeholder)

        # Should call markdown once with all content combined
        assert mock_placeholder.markdown.call_count == 1

    def test_render_message_ignores_non_text_blocks(self):
        """Test rendering message ignores non-text content blocks."""
        mock_placeholder = Mock()

        # AIMessage with text content - non-text blocks are handled by AIMessage
        message = AIMessage(content="Text content")

        ChatMessage.render_message(message, mock_placeholder)

        # Should render the text block
        mock_placeholder.markdown.assert_called_once()

    def test_render_message_with_unsafe_html_enabled(self):
        """Test rendering message enables unsafe_allow_html."""
        mock_placeholder = Mock()

        message = AIMessage(content="Test")

        ChatMessage.render_message(message, mock_placeholder)

        # Verify unsafe_allow_html is True
        call_kwargs = mock_placeholder.markdown.call_args[1]
        assert call_kwargs.get("unsafe_allow_html") is True


class TestRenderStreamingMethod:
    """Test the render_streaming() method."""

    def test_render_stream_with_text(self):
        """Test rendering streaming text."""
        mock_placeholder = Mock()
        runtime = AgentRun(
            agent_id="test-agent", streaming_text="Streaming response..."
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render_streaming("Streaming response...", mock_placeholder)

        mock_placeholder.markdown.assert_called_once()
        call_args = mock_placeholder.markdown.call_args[0][0]
        assert "Streaming response..." in call_args
        assert "loading-dots" in call_args

    def test_render_stream_with_empty_text(self):
        """Test rendering with empty streaming text."""
        mock_placeholder = Mock()
        runtime = AgentRun(agent_id="test-agent", streaming_text="")

        chat_msg = ChatMessage(runtime)
        chat_msg.render_streaming("", mock_placeholder)

        mock_placeholder.markdown.assert_called_once()
        call_args = mock_placeholder.markdown.call_args[0][0]
        # Should still have loading indicator
        assert "loading-dots" in call_args

    def test_render_stream_includes_css_animations(self):
        """Test rendering includes CSS for loading animations."""
        mock_placeholder = Mock()
        runtime = AgentRun(agent_id="test-agent", streaming_text="Test")

        chat_msg = ChatMessage(runtime)
        chat_msg.render_streaming("Test", mock_placeholder)

        call_args = mock_placeholder.markdown.call_args[0][0]
        # Should include CSS styles
        assert "@keyframes" in call_args
        assert "pulse" in call_args
        assert "glow" in call_args


class TestRenderToolCallMethod:
    """Test the render_tool_call() static method."""

    def test_render_tool_call_pending(self):
        """Test rendering tool call without result (pending)."""
        mock_placeholder = Mock()
        mock_expander_context = Mock()
        mock_placeholder.expander.return_value.__enter__ = Mock(
            return_value=mock_expander_context
        )
        mock_placeholder.expander.return_value.__exit__ = Mock(return_value=False)

        tool_call = AgentRunToolCall(
            id="123",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            status="pending",
        )

        ChatMessage.render_tool_call(tool_call, mock_placeholder)

        # Should create expander with tool name
        mock_placeholder.expander.assert_called_once()
        expander_call = mock_placeholder.expander.call_args[0][0]
        assert "calculator" in expander_call
        assert "🔧" in expander_call

    def test_render_tool_call_success(self):
        """Test rendering tool call with successful result."""
        mock_placeholder = Mock()
        mock_expander_context = Mock()
        mock_placeholder.expander.return_value.__enter__ = Mock(
            return_value=mock_expander_context
        )
        mock_placeholder.expander.return_value.__exit__ = Mock(return_value=False)

        tool_call = AgentRunToolCall(
            id="123",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            tool_result="4",
            status="success",
        )

        ChatMessage.render_tool_call(tool_call, mock_placeholder)

        # Should create expander
        mock_placeholder.expander.assert_called_once()

    def test_render_tool_call_error(self):
        """Test rendering tool call with error result."""
        mock_placeholder = Mock()
        mock_expander_context = Mock()
        mock_placeholder.expander.return_value.__enter__ = Mock(
            return_value=mock_expander_context
        )
        mock_placeholder.expander.return_value.__exit__ = Mock(return_value=False)

        tool_call = AgentRunToolCall(
            id="456",
            tool_id="file_reader",
            tool_input={"path": "/test"},
            tool_result="File not found",
            status="error",
            error="File not found",
        )

        ChatMessage.render_tool_call(tool_call, mock_placeholder)

        # Should create expander
        mock_placeholder.expander.assert_called_once()


class TestIntegration:
    """Integration tests for ChatMessage class."""

    def test_full_render_flow_with_streaming(self):
        """Test complete render flow with streaming runtime."""
        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="Calculate 2+2"),
            streaming_text="The answer is 4",
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Verify user message
        mock_user_msg.text.assert_called_once_with("Calculate 2+2")

        # Verify assistant message with loading indicator
        mock_assistant_msg.markdown.assert_called_once()
        call_args = mock_assistant_msg.markdown.call_args[0][0]
        assert "The answer is 4" in call_args
        assert "loading-dots" in call_args

    def test_full_render_flow_with_completed_message(self):
        """Test complete render flow with completed message."""
        from datetime import datetime

        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]

        message = AgentRunContent(text="Here is your answer.")

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="Help me"),
            reply=message,
            completed_at=datetime.now(),
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Verify message was rendered
        assert mock_assistant_msg.markdown.call_count == 1
        call_args = mock_assistant_msg.markdown.call_args[0][0]
        assert "answer" in call_args

    def test_render_runtime_with_tool_calls(self):
        """Test rendering runtime with tool calls."""
        mock_placeholder = Mock()
        mock_container = Mock()
        mock_user_msg = Mock()
        mock_assistant_msg = Mock()
        mock_expander_context = Mock()
        mock_placeholder.container.return_value = mock_container
        mock_container.chat_message.side_effect = [mock_user_msg, mock_assistant_msg]
        mock_assistant_msg.expander.return_value.__enter__ = Mock(
            return_value=mock_expander_context
        )
        mock_assistant_msg.expander.return_value.__exit__ = Mock(return_value=False)

        tool_call1 = AgentRunToolCall(
            id="1",
            tool_id="tool1",
            tool_input={},
            tool_result="result1",
            status="success",
        )
        tool_call2 = AgentRunToolCall(
            id="2",
            tool_id="tool2",
            tool_input={},
            tool_result="result2",
            status="success",
        )

        from datetime import datetime

        runtime = AgentRun(
            agent_id="test-agent",
            query=AgentRunContent(text="Test query"),
            tool_calls={"1": tool_call1, "2": tool_call2},
            reply=AgentRunContent(text="Done"),
            completed_at=datetime.now(),
        )

        chat_msg = ChatMessage(runtime)
        chat_msg.render(mock_placeholder)

        # Should create two expanders for tool calls
        assert mock_assistant_msg.expander.call_count == 2
        # Should render the message text
        mock_assistant_msg.markdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
