#!/usr/bin/env python3
"""
Regression tests for agent run persistence fix.

Tests verify that when an agent completes execution (successfully or with errors),
the final agent run state is properly saved to the repository with:
- status set to "completed" or "failed" (not "executing")
- completed_at timestamp populated (not null)
- reply field containing the agent's response (not null)
- is_completed set to true

These tests prevent regression of the bug where agent run final states were not
being persisted to the repository after the FINISH event.
"""

import tempfile
import json
from datetime import datetime
from pathlib import Path

from fivcplayground.agents import (
    AgentRunSessionSpan,
)
from fivcplayground.agents.types import (
    AgentRun,
    AgentRunContent,
    AgentRunStatus,
    AgentRunSession,
)
from fivcplayground.agents.types.repositories import (
    FileAgentRunRepository,
)
from fivcplayground.utils import OutputDir


class TestAgentRunFinalStatePersistence:
    """Test that agent run final state is persisted to repository."""

    def test_agent_run_session_span_saves_on_call(self):
        """Test that AgentRunSessionSpan saves agent run when called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-123"
            agent_id = "test-agent"

            # Create a session first
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Create an agent run with final state
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.COMPLETED,
                query=AgentRunContent(text="test query"),
                reply=AgentRunContent(text="test response"),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            # Create AgentRunSessionSpan and call it to save
            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Verify the agent run was saved
            saved_run = repo.get_agent_run(session_id, agent_run.id)
            assert saved_run is not None
            assert saved_run.status == AgentRunStatus.COMPLETED
            assert saved_run.reply is not None
            assert saved_run.reply.text == "test response"
            assert saved_run.completed_at is not None

    def test_agent_run_json_file_contains_final_state(self):
        """Test that persisted JSON file contains final state with reply."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-456"
            agent_id = "test-agent"

            # Create session
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Create and save agent run with final state
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.COMPLETED,
                query=AgentRunContent(text="hello"),
                reply=AgentRunContent(text="hello there"),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Find and read the JSON file
            session_dir = Path(tmpdir) / f"session_{session_id}"
            json_files = list(session_dir.glob("run_*.json"))
            assert len(json_files) > 0

            # Verify JSON file contains final state
            with open(json_files[0]) as f:
                data = json.load(f)

            assert data["status"] == "completed"
            assert data["completed_at"] is not None
            assert data["reply"] is not None
            assert data["reply"]["text"] == "hello there"
            assert data["is_completed"] is True

    def test_agent_run_failed_status_persisted(self):
        """Test that failed agent runs are persisted with error status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-789"
            agent_id = "test-agent"

            # Create session
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Create failed agent run
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.FAILED,
                query=AgentRunContent(text="test"),
                error="Test error occurred",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Verify failed state was persisted
            saved_run = repo.get_agent_run(session_id, agent_run.id)
            assert saved_run is not None
            assert saved_run.status == AgentRunStatus.FAILED
            assert saved_run.error == "Test error occurred"
            assert saved_run.completed_at is not None
            assert saved_run.is_completed is True


class TestAgentRunFinishEventPersistence:
    """Test that FINISH event properly triggers repository save."""

    def test_finish_event_callback_saves_agent_run(self):
        """Test that FINISH event callback saves agent run to repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-finish"
            agent_id = "test-agent"

            # Create session
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Simulate FINISH event callback
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.COMPLETED,
                query=AgentRunContent(text="test"),
                reply=AgentRunContent(text="response"),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            # Create span and simulate event callback
            # The span's __call__ method is invoked with just the agent_run
            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Verify agent run was saved
            saved_run = repo.get_agent_run(session_id, agent_run.id)
            assert saved_run is not None
            assert saved_run.status == AgentRunStatus.COMPLETED
            assert saved_run.reply is not None

    def test_agent_run_without_repository_doesnt_crash(self):
        """Test that agent run without repository doesn't crash."""
        # Create span with None repository
        span = AgentRunSessionSpan(None, None, None)

        agent_run = AgentRun(
            agent_id="test",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text="test"),
            reply=AgentRunContent(text="response"),
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

        # Should not raise exception
        span(agent_run)

    def test_agent_run_without_session_id_doesnt_crash(self):
        """Test that agent run without session ID doesn't crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create span with None session ID
            span = AgentRunSessionSpan(repo, None, "test-agent")

            agent_run = AgentRun(
                agent_id="test",
                status=AgentRunStatus.COMPLETED,
                query=AgentRunContent(text="test"),
                reply=AgentRunContent(text="response"),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            # Should not raise exception
            span(agent_run)


class TestAgentRunErrorScenarios:
    """Test agent run persistence in error scenarios."""

    def test_agent_run_with_exception_still_persists(self):
        """Test that agent run is persisted even if exception occurs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-error"
            agent_id = "test-agent"

            # Create session
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Create agent run that represents an error state
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.FAILED,
                query=AgentRunContent(text="test"),
                error="Exception: Something went wrong",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            # Save via span
            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Verify error state was persisted
            saved_run = repo.get_agent_run(session_id, agent_run.id)
            assert saved_run is not None
            assert saved_run.status == AgentRunStatus.FAILED
            assert saved_run.error is not None
            assert "Exception" in saved_run.error
            assert saved_run.completed_at is not None

    def test_agent_run_reply_not_null_after_completion(self):
        """Test that reply field is not null after agent completion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            session_id = "test-session-reply"
            agent_id = "test-agent"

            # Create session
            repo.update_agent_run_session(
                AgentRunSession(
                    id=session_id,
                    agent_id=agent_id,
                    started_at=datetime.now(),
                )
            )

            # Create agent run with reply
            agent_run = AgentRun(
                agent_id=agent_id,
                status=AgentRunStatus.COMPLETED,
                query=AgentRunContent(text="What is 2+2?"),
                reply=AgentRunContent(text="2+2 equals 4"),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            span = AgentRunSessionSpan(repo, session_id, agent_id)
            span(agent_run)

            # Verify reply is not null
            saved_run = repo.get_agent_run(session_id, agent_run.id)
            assert saved_run.reply is not None
            assert saved_run.reply.text == "2+2 equals 4"
            assert saved_run.is_completed is True
