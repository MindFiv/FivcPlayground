"""
Tests for SqliteAgentsRuntimeRepository implementation.

Tests verify that the SQLite-based repository correctly implements
the AgentsRuntimeRepository interface with proper data persistence,
retrieval, and cascading deletes.
"""

import tempfile
import pytest
from datetime import datetime

from fivcplayground.agents.types import (
    AgentsRuntimeMeta,
    AgentsRuntime,
    AgentsRuntimeToolCall,
    AgentsStatus,
    AgentsContent,
)
from fivcplayground.agents.types.repositories import SqliteAgentsRuntimeRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from fivcplayground.utils import OutputDir

        output_dir = OutputDir(tmpdir)
        repo = SqliteAgentsRuntimeRepository(output_dir=output_dir)
        yield repo
        repo.close()


class TestAgentOperations:
    """Test agent metadata operations."""

    def test_update_and_get_agent(self, temp_db):
        """Test creating and retrieving agent metadata."""
        agent = AgentsRuntimeMeta(
            agent_id="test-agent",
            agent_name="Test Agent",
            system_prompt="You are a test agent",
            description="A test agent for testing",
        )

        temp_db.update_agent(agent)
        retrieved = temp_db.get_agent("test-agent")

        assert retrieved is not None
        assert retrieved.agent_id == "test-agent"
        assert retrieved.agent_name == "Test Agent"
        assert retrieved.system_prompt == "You are a test agent"
        assert retrieved.description == "A test agent for testing"

    def test_get_nonexistent_agent(self, temp_db):
        """Test retrieving a non-existent agent returns None."""
        result = temp_db.get_agent("nonexistent")
        assert result is None

    def test_list_agents(self, temp_db):
        """Test listing all agents."""
        agents_data = [
            ("agent-1", "Agent 1"),
            ("agent-2", "Agent 2"),
            ("agent-3", "Agent 3"),
        ]

        for agent_id, agent_name in agents_data:
            agent = AgentsRuntimeMeta(
                agent_id=agent_id,
                agent_name=agent_name,
            )
            temp_db.update_agent(agent)

        agents = temp_db.list_agents()
        assert len(agents) == 3
        assert agents[0].agent_id == "agent-1"
        assert agents[1].agent_id == "agent-2"
        assert agents[2].agent_id == "agent-3"

    def test_delete_agent(self, temp_db):
        """Test deleting an agent."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        assert temp_db.get_agent("test-agent") is not None

        temp_db.delete_agent("test-agent")
        assert temp_db.get_agent("test-agent") is None

    def test_delete_nonexistent_agent(self, temp_db):
        """Test deleting a non-existent agent doesn't raise error."""
        # Should not raise any exception
        temp_db.delete_agent("nonexistent")


class TestAgentRuntimeOperations:
    """Test agent runtime operations."""

    def test_update_and_get_runtime(self, temp_db):
        """Test creating and retrieving agent runtime."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(
            agent_id="test-agent",
            agent_name="Test Agent",
            status=AgentsStatus.EXECUTING,
            query=AgentsContent(text="What is 2+2?"),
        )

        temp_db.update_agent_runtime("test-agent", runtime)
        retrieved = temp_db.get_agent_runtime("test-agent", runtime.agent_run_id)

        assert retrieved is not None
        assert retrieved.agent_id == "test-agent"
        assert retrieved.status == AgentsStatus.EXECUTING
        assert retrieved.query is not None
        assert retrieved.query.text == "What is 2+2?"

    def test_list_agent_runtimes(self, temp_db):
        """Test listing all runtimes for an agent."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        # Create multiple runtimes
        runtime_ids = []
        for i in range(3):
            runtime = AgentsRuntime(
                agent_id="test-agent",
                agent_name="Test Agent",
                query=AgentsContent(text=f"Query {i}"),
            )
            temp_db.update_agent_runtime("test-agent", runtime)
            runtime_ids.append(runtime.agent_run_id)

        runtimes = temp_db.list_agent_runtimes("test-agent")
        assert len(runtimes) == 3
        assert runtimes[0].agent_run_id == runtime_ids[0]

    def test_delete_agent_runtime(self, temp_db):
        """Test deleting an agent runtime."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        assert temp_db.get_agent_runtime("test-agent", runtime.agent_run_id) is not None

        temp_db.delete_agent_runtime("test-agent", runtime.agent_run_id)
        assert temp_db.get_agent_runtime("test-agent", runtime.agent_run_id) is None


class TestToolCallOperations:
    """Test tool call operations."""

    def test_update_and_get_tool_call(self, temp_db):
        """Test creating and retrieving tool calls."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        tool_call = AgentsRuntimeToolCall(
            tool_use_id="call-1",
            tool_name="calculator",
            tool_input={"expression": "2+2"},
            status="pending",
        )

        temp_db.update_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, tool_call
        )
        retrieved = temp_db.get_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, "call-1"
        )

        assert retrieved is not None
        assert retrieved.tool_use_id == "call-1"
        assert retrieved.tool_name == "calculator"
        assert retrieved.tool_input == {"expression": "2+2"}
        assert retrieved.status == "pending"

    def test_list_tool_calls(self, temp_db):
        """Test listing all tool calls for a runtime."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        # Create multiple tool calls
        for i in range(3):
            tool_call = AgentsRuntimeToolCall(
                tool_use_id=f"call-{i}",
                tool_name="calculator",
                tool_input={"expression": f"{i}+{i}"},
            )
            temp_db.update_agent_runtime_tool_call(
                "test-agent", runtime.agent_run_id, tool_call
            )

        tool_calls = temp_db.list_agent_runtime_tool_calls(
            "test-agent", runtime.agent_run_id
        )
        assert len(tool_calls) == 3
        assert tool_calls[0].tool_use_id == "call-0"

    def test_update_tool_call_status(self, temp_db):
        """Test updating tool call status."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        tool_call = AgentsRuntimeToolCall(
            tool_use_id="call-1",
            tool_name="calculator",
            tool_input={"expression": "2+2"},
            status="pending",
        )

        temp_db.update_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, tool_call
        )

        # Update status
        tool_call.status = "success"
        tool_call.tool_result = 4
        tool_call.completed_at = datetime.now()

        temp_db.update_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, tool_call
        )

        retrieved = temp_db.get_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, "call-1"
        )
        assert retrieved.status == "success"
        assert retrieved.tool_result == 4


class TestCascadingDeletes:
    """Test cascading delete behavior."""

    def test_delete_agent_cascades_to_runtimes(self, temp_db):
        """Test that deleting an agent deletes all its runtimes."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        assert len(temp_db.list_agent_runtimes("test-agent")) == 1

        temp_db.delete_agent("test-agent")

        assert len(temp_db.list_agent_runtimes("test-agent")) == 0

    def test_delete_runtime_cascades_to_tool_calls(self, temp_db):
        """Test that deleting a runtime deletes all its tool calls."""
        agent = AgentsRuntimeMeta(agent_id="test-agent")
        temp_db.update_agent(agent)

        runtime = AgentsRuntime(agent_id="test-agent")
        temp_db.update_agent_runtime("test-agent", runtime)

        tool_call = AgentsRuntimeToolCall(
            tool_use_id="call-1",
            tool_name="calculator",
        )
        temp_db.update_agent_runtime_tool_call(
            "test-agent", runtime.agent_run_id, tool_call
        )

        assert (
            len(
                temp_db.list_agent_runtime_tool_calls(
                    "test-agent", runtime.agent_run_id
                )
            )
            == 1
        )

        temp_db.delete_agent_runtime("test-agent", runtime.agent_run_id)

        assert (
            len(
                temp_db.list_agent_runtime_tool_calls(
                    "test-agent", runtime.agent_run_id
                )
            )
            == 0
        )


class TestDataPersistence:
    """Test data persistence across connections."""

    def test_data_persists_across_connections(self):
        """Test that data persists when reopening the database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from fivcplayground.utils import OutputDir

            output_dir = OutputDir(tmpdir)

            # Create and store data
            repo1 = SqliteAgentsRuntimeRepository(output_dir=output_dir)
            agent = AgentsRuntimeMeta(
                agent_id="test-agent",
                agent_name="Test Agent",
            )
            repo1.update_agent(agent)
            repo1.close()

            # Reopen and verify data
            repo2 = SqliteAgentsRuntimeRepository(output_dir=output_dir)
            retrieved = repo2.get_agent("test-agent")

            assert retrieved is not None
            assert retrieved.agent_name == "Test Agent"
            repo2.close()


class TestForeignKeyConstraints:
    """Test foreign key constraint handling."""

    def test_create_runtime_without_agent(self, temp_db):
        """Test that runtime can be created without explicitly creating agent first.

        This tests the fix for the FOREIGN KEY constraint issue where
        update_agent_runtime should automatically create the agent if it doesn't exist.
        """
        # Create runtime without creating agent first
        runtime = AgentsRuntime(
            agent_id="auto-created-agent",
            agent_name="Auto Created Agent",
            status=AgentsStatus.EXECUTING,
            query=AgentsContent(text="Test query"),
            started_at=datetime.now(),
        )

        # This should not raise a FOREIGN KEY constraint error
        temp_db.update_agent_runtime("auto-created-agent", runtime)

        # Verify runtime was created
        retrieved_runtime = temp_db.get_agent_runtime(
            "auto-created-agent", runtime.agent_run_id
        )
        assert retrieved_runtime is not None
        assert retrieved_runtime.agent_id == "auto-created-agent"

        # Verify agent was auto-created
        agent = temp_db.get_agent("auto-created-agent")
        assert agent is not None
        assert agent.agent_id == "auto-created-agent"

    def test_create_tool_call_without_runtime(self, temp_db):
        """Test that tool call can be created without explicitly creating runtime first.

        This tests the fix for the FOREIGN KEY constraint issue where
        update_agent_runtime_tool_call should automatically create the runtime if it doesn't exist.
        """
        # Create tool call without creating runtime first
        tool_call = AgentsRuntimeToolCall(
            tool_use_id="tool-1",
            tool_name="test_tool",
            tool_input={"param": "value"},
            status="pending",
        )

        # This should not raise a FOREIGN KEY constraint error
        temp_db.update_agent_runtime_tool_call(
            "auto-created-agent", "auto-created-run", tool_call
        )

        # Verify tool call was created
        retrieved_tool_call = temp_db.get_agent_runtime_tool_call(
            "auto-created-agent", "auto-created-run", "tool-1"
        )
        assert retrieved_tool_call is not None
        assert retrieved_tool_call.tool_use_id == "tool-1"

        # Verify runtime was auto-created
        runtime = temp_db.get_agent_runtime("auto-created-agent", "auto-created-run")
        assert runtime is not None
        assert runtime.agent_run_id == "auto-created-run"
