"""
Tests for SqliteAgentRunRepository implementation.

Tests verify that the SQLite-based repository correctly implements
the AgentRunRepository interface with proper data persistence,
retrieval, and cascading deletes.
"""

import tempfile
import pytest
from datetime import datetime

from fivcplayground.agents.types import (
    AgentRunSession,
    AgentRun,
    AgentRunToolCall,
    AgentRunStatus,
    AgentRunContent,
)
from fivcplayground.agents.types.repositories import SqliteAgentRunRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from fivcplayground.utils import OutputDir

        output_dir = OutputDir(tmpdir)
        repo = SqliteAgentRunRepository(output_dir=output_dir)
        yield repo
        repo.close()


class TestAgentOperations:
    """Test agent metadata operations."""

    def test_update_and_get_agent(self, temp_db):
        """Test creating and retrieving agent metadata."""
        agent = AgentRunSession(
            agent_id="test-agent",
            description="A test agent for testing",
        )

        temp_db.update_agent_run_session(agent)
        retrieved = temp_db.get_agent_run_session(agent.id)

        assert retrieved is not None
        assert retrieved.agent_id == "test-agent"
        assert retrieved.description == "A test agent for testing"

    def test_get_nonexistent_agent(self, temp_db):
        """Test retrieving a non-existent agent returns None."""
        result = temp_db.get_agent_run_session("nonexistent-session-id")
        assert result is None

    def test_list_agents(self, temp_db):
        """Test listing all agents."""
        agents_data = [
            ("agent-1", "Agent 1"),
            ("agent-2", "Agent 2"),
            ("agent-3", "Agent 3"),
        ]

        for agent_id, description in agents_data:
            agent = AgentRunSession(
                agent_id=agent_id,
                description=description,
            )
            temp_db.update_agent_run_session(agent)

        agents = temp_db.list_agent_run_sessions()
        assert len(agents) == 3
        assert agents[0].agent_id == "agent-1"
        assert agents[1].agent_id == "agent-2"
        assert agents[2].agent_id == "agent-3"

    def test_delete_agent(self, temp_db):
        """Test deleting an agent session."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        # Create a runtime for this session
        from fivcplayground.agents.types import AgentRun

        runtime = AgentRun(agent_id="test-agent")
        temp_db.update_agent_run(agent.id, runtime)

        assert temp_db.get_agent_run_session(agent.id) is not None

        temp_db.delete_agent_run_session(agent.id)
        assert temp_db.get_agent_run_session(agent.id) is None

    def test_delete_nonexistent_agent(self, temp_db):
        """Test deleting a non-existent agent doesn't raise error."""
        # Should not raise any exception
        temp_db.delete_agent_run_session("nonexistent-session-id")


class TestAgentRuntimeOperations:
    """Test agent runtime operations."""

    def test_update_and_get_runtime(self, temp_db):
        """Test creating and retrieving agent runtime."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(
            agent_id="test-agent",
            status=AgentRunStatus.EXECUTING,
            query=AgentRunContent(text="What is 2+2?"),
        )

        temp_db.update_agent_run(agent.id, runtime)
        retrieved = temp_db.get_agent_run(agent.id, runtime.id)

        assert retrieved is not None
        assert retrieved.agent_id == "test-agent"
        assert retrieved.status == AgentRunStatus.EXECUTING
        assert retrieved.query is not None
        assert retrieved.query.text == "What is 2+2?"

    def test_list_agent_runtimes(self, temp_db):
        """Test listing all runtimes for an agent."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        # Create multiple runtimes
        runtime_ids = []
        for i in range(3):
            runtime = AgentRun(
                agent_id="test-agent",
                query=AgentRunContent(text=f"Query {i}"),
            )
            temp_db.update_agent_run(agent.id, runtime)
            runtime_ids.append(runtime.id)

        runtimes = temp_db.list_agent_runs(agent.id)
        assert len(runtimes) == 3
        assert runtimes[0].id == runtime_ids[0]

    def test_delete_agent_runtime(self, temp_db):
        """Test deleting an agent runtime."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")
        temp_db.update_agent_run(agent.id, runtime)

        assert temp_db.get_agent_run(agent.id, runtime.id) is not None

        temp_db.delete_agent_run(agent.id, runtime.id)
        assert temp_db.get_agent_run(agent.id, runtime.id) is None


class TestToolCallOperations:
    """Test tool call operations."""

    def test_update_and_get_tool_call(self, temp_db):
        """Test creating and retrieving tool calls (embedded)."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")

        # Create tool call and embed it
        tool_call = AgentRunToolCall(
            id="call-1",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            status="pending",
        )
        runtime.tool_calls["call-1"] = tool_call

        temp_db.update_agent_run(agent.id, runtime)

        # Retrieve runtime and check embedded tool call
        retrieved_runtime = temp_db.get_agent_run(agent.id, runtime.id)

        assert retrieved_runtime is not None
        assert "call-1" in retrieved_runtime.tool_calls
        retrieved = retrieved_runtime.tool_calls["call-1"]
        assert retrieved.id == "call-1"
        assert retrieved.tool_id == "calculator"
        assert retrieved.tool_input == {"expression": "2+2"}
        assert retrieved.status == "pending"

    def test_list_tool_calls(self, temp_db):
        """Test listing all tool calls for a runtime (embedded)."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")

        # Create multiple tool calls and embed them
        for i in range(3):
            tool_call = AgentRunToolCall(
                id=f"call-{i}",
                tool_id="calculator",
                tool_input={"expression": f"{i}+{i}"},
            )
            runtime.tool_calls[f"call-{i}"] = tool_call

        temp_db.update_agent_run(agent.id, runtime)

        # Retrieve runtime and check embedded tool calls
        retrieved_runtime = temp_db.get_agent_run(agent.id, runtime.id)
        tool_calls = list(retrieved_runtime.tool_calls.values())
        assert len(tool_calls) == 3
        # Check that all tool calls are present
        tool_call_ids = {tc.id for tc in tool_calls}
        assert "call-0" in tool_call_ids
        assert "call-1" in tool_call_ids
        assert "call-2" in tool_call_ids

    def test_update_tool_call_status(self, temp_db):
        """Test updating tool call status (embedded)."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")

        tool_call = AgentRunToolCall(
            id="call-1",
            tool_id="calculator",
            tool_input={"expression": "2+2"},
            status="pending",
        )
        runtime.tool_calls["call-1"] = tool_call
        temp_db.update_agent_run(agent.id, runtime)

        # Update status
        tool_call.status = "success"
        tool_call.tool_result = 4
        tool_call.completed_at = datetime.now()
        runtime.tool_calls["call-1"] = tool_call

        temp_db.update_agent_run(agent.id, runtime)

        # Retrieve and verify
        retrieved_runtime = temp_db.get_agent_run(agent.id, runtime.id)
        retrieved = retrieved_runtime.tool_calls["call-1"]
        assert retrieved.status == "success"
        assert retrieved.tool_result == 4


class TestCascadingDeletes:
    """Test cascading delete behavior."""

    def test_delete_agent_cascades_to_runtimes(self, temp_db):
        """Test that deleting an agent session deletes all its runtimes."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")
        temp_db.update_agent_run(agent.id, runtime)

        assert len(temp_db.list_agent_runs(agent.id)) == 1

        temp_db.delete_agent_run_session(agent.id)

        assert len(temp_db.list_agent_runs(agent.id)) == 0

    def test_delete_runtime_cascades_to_tool_calls(self, temp_db):
        """Test that deleting a runtime deletes all its tool calls (embedded)."""
        agent = AgentRunSession(agent_id="test-agent")
        temp_db.update_agent_run_session(agent)

        runtime = AgentRun(agent_id="test-agent")

        # Create tool call and embed it
        tool_call = AgentRunToolCall(
            id="call-1",
            tool_id="calculator",
        )
        runtime.tool_calls["call-1"] = tool_call

        temp_db.update_agent_run(agent.id, runtime)

        # Verify tool call exists
        retrieved_runtime = temp_db.get_agent_run(agent.id, runtime.id)
        assert len(retrieved_runtime.tool_calls) == 1

        # Delete runtime
        temp_db.delete_agent_run(agent.id, runtime.id)

        # Verify runtime and tool calls are deleted
        assert temp_db.get_agent_run(agent.id, runtime.id) is None


class TestDataPersistence:
    """Test data persistence across connections."""

    def test_data_persists_across_connections(self):
        """Test that data persists when reopening the database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from fivcplayground.utils import OutputDir

            output_dir = OutputDir(tmpdir)

            # Create and store data
            repo1 = SqliteAgentRunRepository(output_dir=output_dir)
            agent = AgentRunSession(
                agent_id="test-agent",
                description="Test Agent",
            )
            repo1.update_agent_run_session(agent)

            # Create a runtime for this session
            from fivcplayground.agents.types import AgentRun

            runtime = AgentRun(agent_id="test-agent")
            repo1.update_agent_run(agent.id, runtime)
            repo1.close()

            # Reopen and verify data
            repo2 = SqliteAgentRunRepository(output_dir=output_dir)
            retrieved = repo2.get_agent_run_session(agent.id)

            assert retrieved is not None
            assert retrieved.description == "Test Agent"
            repo2.close()


class TestForeignKeyConstraints:
    """Test foreign key constraint handling."""

    def test_create_runtime_without_agent(self, temp_db):
        """Test that runtime can be created without explicitly creating agent first.

        This tests the fix for the FOREIGN KEY constraint issue where
        update_agent_run should automatically create the agent if it doesn't exist.
        """
        # Create a session first
        agent = AgentRunSession(agent_id="auto-created-agent")
        temp_db.update_agent_run_session(agent)

        # Create runtime
        runtime = AgentRun(
            agent_id="auto-created-agent",
            status=AgentRunStatus.EXECUTING,
            query=AgentRunContent(text="Test query"),
            started_at=datetime.now(),
        )

        # This should not raise a FOREIGN KEY constraint error
        temp_db.update_agent_run(agent.id, runtime)

        # Verify runtime was created
        retrieved_runtime = temp_db.get_agent_run(agent.id, runtime.id)
        assert retrieved_runtime is not None
        assert retrieved_runtime.agent_id == "auto-created-agent"

        # Verify agent was created
        retrieved_agent = temp_db.get_agent_run_session(agent.id)
        assert retrieved_agent is not None
        assert retrieved_agent.agent_id == "auto-created-agent"

    def test_create_tool_call_without_runtime(self, temp_db):
        """Test that tool calls are embedded in runtime (no separate creation).

        With the new embedded tool calls design, tool calls are part of the runtime
        and cannot be created independently.
        """
        # Create a session first
        agent = AgentRunSession(agent_id="auto-created-agent")
        temp_db.update_agent_run_session(agent)

        # Create runtime with embedded tool call
        runtime = AgentRun(agent_id="auto-created-agent", id="auto-created-run")

        tool_call = AgentRunToolCall(
            id="tool-1",
            tool_id="test_tool",
            tool_input={"param": "value"},
            status="pending",
        )
        runtime.tool_calls["tool-1"] = tool_call

        # Update runtime with embedded tool call using session_id
        temp_db.update_agent_run(agent.id, runtime)

        # Verify runtime and embedded tool call were created
        retrieved_runtime = temp_db.get_agent_run(agent.id, "auto-created-run")
        assert retrieved_runtime is not None
        assert retrieved_runtime.id == "auto-created-run"
        assert "tool-1" in retrieved_runtime.tool_calls
        assert retrieved_runtime.tool_calls["tool-1"].id == "tool-1"
