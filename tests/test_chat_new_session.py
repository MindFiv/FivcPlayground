#!/usr/bin/env python3
"""
Tests for Chat class new session creation functionality.

Tests that when a new chat is created and the agent responds,
the Chat.id property is properly updated to reflect the new session ID.
"""

import tempfile
import asyncio
from unittest.mock import Mock, AsyncMock

from fivcplayground.demos.utils import Chat
from fivcplayground.agents.types import (
    AgentRunContent,
    AgentRunSession,
)
from fivcplayground.agents.types.repositories import FileAgentRunRepository
from fivcplayground.utils import OutputDir


class TestChatNewSession:
    """Test Chat class new session creation."""

    def test_chat_id_is_none_initially(self):
        """Test that a new Chat has id=None initially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a new chat without session ID
            chat = Chat(
                agent_runnable=Mock(),
                agent_run_repository=repo,
                briefing_runnable=Mock(),
                tool_retriever=Mock(),
            )

            # Initially, id should be None
            assert chat.id is None

    def test_chat_id_updated_after_ask_async(self):
        """Test that Chat.id is updated after ask_async creates a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a mock runnable that creates a session when run_async is called
            async def mock_run_async(**kwargs):
                # Extract the session ID and repository from kwargs
                session_id = kwargs.get("agent_run_session_id")
                agent_run_repo = kwargs.get("agent_run_repository")
                agent_id = "test-agent"

                # Create the session in the repository (simulating what AgentRunSessionSpan does)
                if session_id and agent_run_repo:
                    agent_run_repo.update_agent_run_session(
                        AgentRunSession(
                            id=session_id,
                            agent_id=agent_id,
                            description="Test chat",
                        )
                    )

                return AgentRunContent(text="Test response")

            mock_runnable = AsyncMock()
            mock_runnable.id = "test-agent"
            mock_runnable.run_async = mock_run_async

            mock_briefing = AsyncMock()
            mock_briefing.run_async = AsyncMock(
                return_value=AgentRunContent(text="Test chat description")
            )

            # Create a new chat without session ID
            chat = Chat(
                agent_runnable=mock_runnable,
                agent_run_repository=repo,
                briefing_runnable=mock_briefing,
                tool_retriever=Mock(),
            )

            # Initially, id should be None
            assert chat.id is None

            # Call ask_async
            result = asyncio.run(chat.ask_async("Test query"))

            # After ask_async, id should be set
            assert result
            assert chat.id is not None
            assert isinstance(chat.id, str)

            # Verify the session was created in the repository
            session = repo.get_agent_run_session(chat.id)
            assert session is not None
            assert session.agent_id == "test-agent"

    def test_chat_id_persists_for_existing_session(self):
        """Test that Chat.id doesn't change for existing sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(
                id="existing-session-123",
                agent_id="test-agent",
                description="Existing chat",
            )
            repo.update_agent_run_session(session)

            # Create a chat with existing session ID
            chat = Chat(
                agent_runnable=Mock(),
                agent_run_repository=repo,
                agent_run_session_id="existing-session-123",
                briefing_runnable=Mock(),
                tool_retriever=Mock(),
            )

            # id should be the existing session ID
            assert chat.id == "existing-session-123"
