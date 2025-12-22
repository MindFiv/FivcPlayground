import re

import streamlit as st
from pydantic import BaseModel
from streamlit.delta_generator import DeltaGenerator

from fivcplayground.agents.types import (
    AgentRunContent,
    AgentRun,
    AgentRunToolCall,
)


class ChatMessage(object):
    """
    Component for rendering chat messages with support for thinking content extraction.

    This class handles the display of chat messages in the FivcPlayground interface, including:
    - User queries and agent responses
    - Tool call execution details in expandable sections
    - LLM thinking content (<think>...</think>) in separate expanders
    - Streaming response rendering with real-time thinking updates

    Class Variables:
        LOADING_INDICATOR (str): CSS and HTML for animated loading dots
        COMPLETE_THINK_PATTERN (str): Regex pattern for complete <think>...</think> blocks
        UNCLOSED_THINK_PATTERN (str): Regex pattern for unclosed <think> tags (streaming)
        WHITESPACE_CLEANUP_PATTERN (str): Regex pattern for cleaning extra whitespace

    Features:
        - Extracts and displays thinking content in collapsible expanders
        - Handles both complete and streaming responses
        - Supports multiple thinking blocks with automatic numbering
        - Shows ongoing thinking in expanded expanders during streaming
        - Renders tool calls with status indicators and timing information

    Example:
        >>> runtime = AgentRun(...)
        >>> chat_msg = ChatMessage(runtime)
        >>> chat_msg.render(st.container())
    """

    # CSS for loading indicator animation
    LOADING_INDICATOR = """
<style>
@keyframes dots {
    0%, 20% {
        content: '●';
    }
    40% {
        content: '●●';
    }
    60%, 100% {
        content: '●●●';
    }
}
@keyframes pulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.7;
        transform: scale(1.15);
    }
}
@keyframes glow {
    0%, 100% {
        text-shadow: 0 0 5px #3498db, 0 0 10px #3498db;
    }
    50% {
        text-shadow: 0 0 10px #3498db, 0 0 20px #3498db, 0 0 30px #5dade2;
    }
}
.loading-dots {
    display: inline-block;
    margin-left: 6px;
    font-size: 1.0em;
    font-weight: bold;
    color: #3498db;
    animation: pulse 1.5s ease-in-out infinite, glow 2s ease-in-out infinite;
}
.loading-dots::after {
    content: '●●●';
    animation: dots 1.2s infinite;
}
</style>
<span class='loading-dots'></span>
"""

    # Regex patterns for thinking content extraction
    COMPLETE_THINK_PATTERN = r"<think\s*>(.*?)</think\s*>"
    UNCLOSED_THINK_PATTERN = r"<think\s*>((?:(?!</think\s*>).)*?)$"
    WHITESPACE_CLEANUP_PATTERN = r"\n\s*\n\s*\n+"

    def __init__(self, runtime: AgentRun):
        self.runtime = runtime

    @classmethod
    def extract_thinking_content(
        cls, text: str, is_streaming: bool = False
    ) -> tuple[str, list[str], str]:
        """
        Extract <think>...</think> content from text and return cleaned text with thinking sections.

        Args:
            text: The input text that may contain <think>...</think> tags
            is_streaming: Whether this is streaming content (handles unclosed tags)

        Returns:
            tuple: (cleaned_text_without_thinking, list_of_completed_thinking_contents, ongoing_thinking_content)
        """
        # Find all complete thinking content using class pattern
        complete_thinking_matches = re.findall(
            cls.COMPLETE_THINK_PATTERN, text, re.DOTALL | re.IGNORECASE
        )

        # Remove complete <think>...</think> sections from the text
        text_without_complete_thinks = re.sub(
            cls.COMPLETE_THINK_PATTERN, "", text, flags=re.DOTALL | re.IGNORECASE
        )

        # Handle unclosed <think> tags for streaming
        ongoing_thinking = ""
        if is_streaming:
            unclosed_match = re.search(
                cls.UNCLOSED_THINK_PATTERN,
                text_without_complete_thinks,
                re.DOTALL | re.IGNORECASE,
            )

            if unclosed_match:
                ongoing_thinking = unclosed_match.group(1).strip()
                # Remove the unclosed <think> section from the main text
                text_without_complete_thinks = re.sub(
                    cls.UNCLOSED_THINK_PATTERN,
                    "",
                    text_without_complete_thinks,
                    flags=re.DOTALL | re.IGNORECASE,
                )

        # Clean up the main text
        cleaned_text = text_without_complete_thinks
        # Clean up extra whitespace - replace multiple consecutive newlines with double newlines
        cleaned_text = re.sub(cls.WHITESPACE_CLEANUP_PATTERN, "\n\n", cleaned_text)
        # Remove leading/trailing whitespace
        cleaned_text = cleaned_text.strip()

        # Clean up thinking content (strip whitespace)
        thinking_contents = [
            content.strip() for content in complete_thinking_matches if content.strip()
        ]

        return cleaned_text, thinking_contents, ongoing_thinking

    def render(self, placeholder: DeltaGenerator):
        placeholder = placeholder.container()

        if self.runtime.query:
            chat_user = placeholder.chat_message("user")
            # Extract text from AgentRunContent
            query_text = (
                self.runtime.query.text
                if hasattr(self.runtime.query, "text")
                else str(self.runtime.query)
            )
            chat_user.text(query_text)

        chat_ai = placeholder.chat_message("assistant")

        # Render tool calls if any
        if self.runtime.tool_calls:
            for tool_call in self.runtime.tool_calls.values():
                self.render_tool_call(tool_call, chat_ai)

        # Render message or streaming text
        if self.runtime.completed_at is not None:
            self.render_message(self.runtime.reply, chat_ai)
        else:
            self.render_streaming(self.runtime.streaming_text, chat_ai)

    @staticmethod
    def render_message(
        message: AgentRunContent | BaseModel,
        placeholder: DeltaGenerator,
    ):
        # Wrap message in adapter for dict-like access
        if isinstance(message, AgentRunContent):
            msg_text = message.text
        elif isinstance(message, BaseModel):
            msg_text = message.model_dump_json()
        else:
            msg_text = str(message)

        # Extract thinking content and clean text (not streaming for completed messages)
        cleaned_text, thinking_contents, _ = ChatMessage.extract_thinking_content(
            msg_text, is_streaming=False
        )

        # Render thinking content in expanders if any
        for i, thinking_content in enumerate(thinking_contents):
            if thinking_content:  # Only render non-empty thinking content
                expander_title = (
                    f"🧠 **Thinking** {i + 1}"
                    if len(thinking_contents) > 1
                    else "🧠 **Thinking**"
                )
                with placeholder.expander(expander_title, expanded=False):
                    st.markdown(thinking_content, unsafe_allow_html=True)

        # Render the main content (without thinking tags)
        if cleaned_text:  # Only render if there's content after removing thinking tags
            placeholder.markdown(cleaned_text, unsafe_allow_html=True)

    @staticmethod
    def render_tool_call(
        tool_call: AgentRunToolCall,
        placeholder: DeltaGenerator,
    ):
        try:
            tool_name = tool_call.tool_id
            tool_id = tool_call.id
            # tool_input = tool_call.tool_input
            tool_result = tool_call.tool_result
            status = tool_call.status

            # Create an expander with the tool name and a tool icon
            with placeholder.expander(f"🔧 **{tool_name}**", expanded=False):
                # Show status
                is_error = status == "error"
                if is_error:
                    st.error("Tool executed with error")
                    if tool_call.error:
                        st.error(f"Error: {tool_call.error}")
                elif status == "success":
                    st.success("Tool executed successfully")
                else:
                    st.info("Tool execution pending...")

                # Show tool ID if available
                if tool_id:
                    st.caption(f"Tool ID: `{tool_id}`")

                # Show timing information if available
                # if tool_call.duration is not None:
                #     st.caption(f"Duration: {tool_call.duration:.3f}s")

                # Show tool input parameters
                # if tool_input:
                #     st.caption("Parameters:")
                #     # Use st.json for nice formatting of the input parameters
                #     st.json(tool_input)
                # else:
                #     st.info("No parameters provided")

                # Show tool result if available
                if tool_result is not None:
                    st.caption("Result:")

                    if isinstance(tool_result, (dict, list)):
                        st.json(tool_result)
                    else:
                        # Display as code block for better formatting
                        st.code(str(tool_result), language="text")
                elif status != "pending":
                    st.info("No result content")

        except Exception as e:
            # Fallback rendering in case of any errors
            st.error(f"Error rendering tool call: {str(e)}")
            st.json(tool_call.model_dump())

    def render_streaming(
        self,
        streaming: str,
        placeholder: DeltaGenerator,
    ):
        # Extract thinking content and clean text for streaming
        cleaned_text, thinking_contents, ongoing_thinking = (
            self.extract_thinking_content(streaming, is_streaming=True)
        )

        # Render completed thinking content in expanders
        for i, thinking_content in enumerate(thinking_contents):
            if thinking_content:  # Only render non-empty thinking content
                expander_title = (
                    f"🧠 **Thinking** {i + 1}"
                    if len(thinking_contents) > 1
                    else "🧠 **Thinking**"
                )
                with placeholder.expander(expander_title, expanded=False):
                    st.markdown(thinking_content, unsafe_allow_html=True)

        # Render ongoing thinking content in an expanded expander if present
        if ongoing_thinking:
            total_thinking_blocks = len(thinking_contents) + 1
            if total_thinking_blocks > 1:
                ongoing_title = f"🧠 **Thinking** {total_thinking_blocks} (ongoing...)"
            else:
                ongoing_title = "🧠 **Thinking** (ongoing...)"

            with placeholder.expander(ongoing_title, expanded=True):
                st.markdown(
                    f"{ongoing_thinking}{ChatMessage.LOADING_INDICATOR}",
                    unsafe_allow_html=True,
                )

        # Render the main streaming content (without thinking tags)
        if cleaned_text:
            streaming_text = f"{cleaned_text}{ChatMessage.LOADING_INDICATOR}"
            placeholder.markdown(streaming_text, unsafe_allow_html=True)
        elif not ongoing_thinking:
            # If no cleaned text and no ongoing thinking, show just the loading indicator
            placeholder.markdown(ChatMessage.LOADING_INDICATOR, unsafe_allow_html=True)
