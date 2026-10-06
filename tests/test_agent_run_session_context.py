"""Tests for persisted AgentRunSession context."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from fivcplayground.agents import AgentRunSession
from fivcplayground.agents.types.repositories import (
    AgentRun,
    FileAgentRunRepository,
    SqliteAgentRunRepository,
)
from fivcplayground.utils import OutputDir


class TestAgentRunSessionContext:
    """Test context behavior across session persistence formats."""

    def test_context_defaults_to_empty_dict(self):
        session = AgentRunSession(agent_id="test-agent")

        assert session.context == {}

    def test_explicit_context_is_retained(self):
        context = {"user_id": "u-123", "metadata": {"locale": "en-US"}}
        session = AgentRunSession(agent_id="test-agent", context=context)

        assert session.context == context

    @pytest.mark.asyncio
    async def test_file_repository_round_trips_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileAgentRunRepository(output_dir=OutputDir(tmpdir))
            session = AgentRunSession(
                agent_id="file-context-agent",
                context={"user_id": "u-123"},
            )

            await repository.update_agent_run_session_async(session)
            retrieved = await repository.get_agent_run_session_async(session.id)
            sessions = await repository.list_agent_run_sessions_async()

            assert retrieved is not None
            assert retrieved.context == {"user_id": "u-123"}
            assert sessions == [retrieved]

    @pytest.mark.asyncio
    async def test_sqlite_repository_round_trips_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repository = SqliteAgentRunRepository(output_dir=output_dir)
            session = AgentRunSession(
                agent_id="sqlite-context-agent",
                context={"user_id": "u-456", "flags": ["beta"]},
            )

            await repository.update_agent_run_session_async(session)
            retrieved = await repository.get_agent_run_session_async(session.id)
            sessions = await repository.list_agent_run_sessions_async()

            connection = sqlite3.connect(repository.db_path)
            try:
                stored_context = connection.execute(
                    "SELECT context FROM agents WHERE session_id = ?",
                    (session.id,),
                ).fetchone()[0]
            finally:
                connection.close()

            assert json.loads(stored_context) == session.context
            assert retrieved is not None
            assert retrieved.context == session.context
            assert sessions == [retrieved]
            repository.close()

    @pytest.mark.asyncio
    async def test_sqlite_placeholder_session_has_empty_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = SqliteAgentRunRepository(output_dir=OutputDir(tmpdir))
            session_id = "placeholder-session"

            await repository.update_agent_run_async(
                session_id,
                AgentRun(agent_id="placeholder-agent"),
            )
            session = await repository.get_agent_run_session_async(session_id)

            assert session is not None
            assert session.context == {}
            repository.close()

    @pytest.mark.asyncio
    async def test_sqlite_migrates_legacy_agents_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            db_path = Path(str(output_dir)) / "agents.db"

            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    """
                    CREATE TABLE agents (
                        id INTEGER PRIMARY KEY,
                        session_id TEXT UNIQUE,
                        agent_id TEXT NOT NULL,
                        system_prompt TEXT,
                        description TEXT,
                        started_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO agents (session_id, agent_id, description)
                    VALUES ('legacy-session', 'legacy-agent', 'Legacy session')
                    """
                )
                connection.commit()
            finally:
                connection.close()

            repository = SqliteAgentRunRepository(output_dir=output_dir)
            session = await repository.get_agent_run_session_async("legacy-session")

            assert session is not None
            assert session.context == {}
            repository.close()
