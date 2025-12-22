#!/usr/bin/env python3
"""
Tests for FileAgentRunRepository functionality.
"""

import tempfile
from datetime import datetime

from fivcplayground.agents.types import (
    AgentRun,
    AgentRunSession,
    AgentRunToolCall,
    AgentRunStatus,
)
from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
from fivcplayground.utils import OutputDir


class TestFileAgentsRuntimeRepository:
    """Tests for FileAgentRunRepository class"""

    def test_initialization(self):
        """Test repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_update_and_get_agent(self):
        """Test creating and retrieving an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-123")
            repo.update_agent_run_session(session)

            # Create an agent runtime
            agent = AgentRun(
                agent_id="test-agent-123",
                status=AgentRunStatus.EXECUTING,
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            # Save agent using session_id
            repo.update_agent_run(session.id, agent)

            # Verify agent file exists in the new structure
            agent_file = repo._get_run_file(session.id, agent.id)
            assert agent_file.exists()

            # Retrieve agent runtime using session_id
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "test-agent-123"
            assert retrieved_agent.status == AgentRunStatus.EXECUTING
            assert retrieved_agent.started_at == datetime(2024, 1, 1, 12, 0, 0)

    def test_get_nonexistent_agent(self):
        """Test retrieving an agent that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent agent using a fake session_id
            agent = repo.get_agent_run("nonexistent-session-id", "nonexistent-run")
            assert agent is None

    def test_delete_agent(self):
        """Test deleting an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-456")
            repo.update_agent_run_session(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-456",
            )
            repo.update_agent_run(session.id, agent)

            # Verify agent exists
            assert repo.get_agent_run(session.id, agent.id) is not None

            # Verify file path
            run_file = repo._get_run_file(session.id, agent.id)
            assert run_file.exists()

            # Delete agent runtime using session_id
            repo.delete_agent_run(session.id, agent.id)

            # Verify agent is deleted
            assert repo.get_agent_run(session.id, agent.id) is None
            assert not run_file.exists()

    def test_update_and_get_tool_call(self):
        """Test creating and retrieving a tool call (embedded in runtime)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-789")
            repo.update_agent_run_session(session)

            # Create an agent first
            agent = AgentRun(
                agent_id="test-agent-789",
            )

            # Create a tool call and embed it in the runtime
            tool_call = AgentRunToolCall(
                id="tool-call-1",
                tool_id="TestTool",
                tool_input={"param": "value"},
                status="pending",
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )
            agent.tool_calls["tool-call-1"] = tool_call

            # Save agent runtime with embedded tool call using session_id
            repo.update_agent_run(session.id, agent)

            # Retrieve agent runtime using session_id
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert retrieved_agent is not None
            assert "tool-call-1" in retrieved_agent.tool_calls

            # Verify tool call data
            retrieved_tool_call = retrieved_agent.tool_calls["tool-call-1"]
            assert retrieved_tool_call.id == "tool-call-1"
            assert retrieved_tool_call.tool_id == "TestTool"
            assert retrieved_tool_call.tool_input == {"param": "value"}
            assert retrieved_tool_call.status == "pending"

    def test_get_nonexistent_tool_call(self):
        """Test retrieving a tool call that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent runtime (which would have no tool calls)
            runtime = repo.get_agent_run("nonexistent-session-id", "nonexistent-run")
            assert runtime is None

    def test_list_tool_calls(self):
        """Test listing all tool calls for an agent runtime (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-999")
            repo.update_agent_run_session(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-999",
            )

            # Create multiple tool calls and embed them in the runtime
            tool_call1 = AgentRunToolCall(
                id="tool-call-1",
                tool_id="Tool1",
                status="pending",
            )
            tool_call2 = AgentRunToolCall(
                id="tool-call-2",
                tool_id="Tool2",
                status="success",
            )
            tool_call3 = AgentRunToolCall(
                id="tool-call-3",
                tool_id="Tool3",
                status="error",
            )

            agent.tool_calls["tool-call-1"] = tool_call1
            agent.tool_calls["tool-call-2"] = tool_call2
            agent.tool_calls["tool-call-3"] = tool_call3

            # Save agent runtime with embedded tool calls using session_id
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify tool calls using session_id
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert len(retrieved_agent.tool_calls) == 3

            tool_call_ids = set(retrieved_agent.tool_calls.keys())
            assert "tool-call-1" in tool_call_ids
            assert "tool-call-2" in tool_call_ids
            assert "tool-call-3" in tool_call_ids

    def test_list_tool_calls_for_nonexistent_agent(self):
        """Test retrieving runtime for an agent that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Get runtime for non-existent session
            runtime = repo.get_agent_run("nonexistent-session-id", "nonexistent-run")
            assert runtime is None

    def test_update_existing_agent(self):
        """Test updating an existing agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-update")
            repo.update_agent_run_session(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-update",
                status=AgentRunStatus.PENDING,
            )
            repo.update_agent_run(session.id, agent)

            # Update agent status
            agent.status = AgentRunStatus.COMPLETED
            agent.completed_at = datetime(2024, 1, 1, 13, 0, 0)
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert retrieved_agent.status == AgentRunStatus.COMPLETED
            assert retrieved_agent.completed_at == datetime(2024, 1, 1, 13, 0, 0)

    def test_update_existing_tool_call(self):
        """Test updating an existing tool call (embedded in runtime)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-tool-update")
            repo.update_agent_run_session(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-tool-update",
            )

            # Create a tool call and embed it
            tool_call = AgentRunToolCall(
                id="tool-call-update",
                tool_id="TestTool",
                status="pending",
            )
            agent.tool_calls["tool-call-update"] = tool_call
            repo.update_agent_run(session.id, agent)

            # Update tool call
            tool_call.status = "success"
            tool_call.completed_at = datetime(2024, 1, 1, 14, 0, 0)
            tool_call.tool_result = {"result": "success"}
            agent.tool_calls["tool-call-update"] = tool_call
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            retrieved_tool_call = retrieved_agent.tool_calls["tool-call-update"]
            assert retrieved_tool_call.status == "success"
            assert retrieved_tool_call.completed_at == datetime(2024, 1, 1, 14, 0, 0)
            assert retrieved_tool_call.tool_result == {"result": "success"}

    def test_delete_agent_with_tool_calls(self):
        """Test deleting an agent that has tool calls (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-with-tools")
            repo.update_agent_run_session(session)

            # Create an agent with embedded tool calls
            agent = AgentRun(
                agent_id="test-agent-with-tools",
            )

            tool_call1 = AgentRunToolCall(id="tool-1", tool_id="Tool1")
            tool_call2 = AgentRunToolCall(id="tool-2", tool_id="Tool2")
            agent.tool_calls["tool-1"] = tool_call1
            agent.tool_calls["tool-2"] = tool_call2

            repo.update_agent_run(session.id, agent)

            # Verify agent and tool calls exist
            retrieved = repo.get_agent_run(session.id, agent.id)
            assert retrieved is not None
            assert len(retrieved.tool_calls) == 2

            # Delete agent runtime
            repo.delete_agent_run(session.id, agent.id)

            # Verify agent and tool calls are deleted
            assert repo.get_agent_run(session.id, agent.id) is None

    def test_storage_structure(self):
        """Test that the storage structure matches the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="structure-test")
            repo.update_agent_run_session(session)

            # Create an agent with embedded tool calls
            agent = AgentRun(
                agent_id="structure-test",
            )

            tool_call = AgentRunToolCall(id="tool-1", tool_id="TestTool")
            agent.tool_calls["tool-1"] = tool_call

            repo.update_agent_run(session.id, agent)

            # Verify new directory structure: session_<id>/run_<id>.json
            session_dir = repo._get_session_dir(session.id)
            assert session_dir.exists()

            run_file = repo._get_run_file(session.id, agent.id)
            assert run_file.exists()
            assert run_file.name == f"run_{agent.id}.json"

    def test_agent_with_streaming_text(self):
        """Test agent runtime with streaming text - verify it's excluded from persistence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="streaming-agent")
            repo.update_agent_run_session(session)

            # Create an agent with streaming text
            agent = AgentRun(
                agent_id="streaming-agent",
                streaming_text="This is streaming text...",
            )
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify
            # streaming_text is excluded from serialization, so it should be empty string (default)
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert retrieved_agent.streaming_text == ""

    def test_agent_with_error(self):
        """Test agent runtime with error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="error-agent")
            repo.update_agent_run_session(session)

            # Create an agent with error
            agent = AgentRun(
                agent_id="error-agent",
                status=AgentRunStatus.FAILED,
                error="Something went wrong",
            )
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            assert retrieved_agent.status == AgentRunStatus.FAILED
            assert retrieved_agent.error == "Something went wrong"

    def test_tool_call_with_complex_input_and_result(self):
        """Test tool call with complex input and result data (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="complex-agent")
            repo.update_agent_run_session(session)

            # Create an agent
            agent = AgentRun(
                agent_id="complex-agent",
            )

            # Create a tool call with complex data and embed it
            tool_call = AgentRunToolCall(
                id="complex-tool-call",
                tool_id="ComplexTool",
                tool_input={
                    "nested": {"data": [1, 2, 3]},
                    "string": "test",
                    "number": 42,
                },
                tool_result={
                    "status": "success",
                    "data": {"items": ["a", "b", "c"]},
                },
                status="success",
            )
            agent.tool_calls["complex-tool-call"] = tool_call
            repo.update_agent_run(session.id, agent)

            # Retrieve and verify
            retrieved_agent = repo.get_agent_run(session.id, agent.id)
            retrieved_tool_call = retrieved_agent.tool_calls["complex-tool-call"]
            assert retrieved_tool_call.tool_input == {
                "nested": {"data": [1, 2, 3]},
                "string": "test",
                "number": 42,
            }
            assert retrieved_tool_call.tool_result == {
                "status": "success",
                "data": {"items": ["a", "b", "c"]},
            }

    def test_delete_nonexistent_agent(self):
        """Test deleting an agent that doesn't exist (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Delete non-existent agent (should not raise error)
            repo.delete_agent_run("nonexistent-session-id", "nonexistent-run")

            # Verify nothing broke
            assert (
                repo.get_agent_run("nonexistent-session-id", "nonexistent-run") is None
            )

    def test_list_agent_runtimes_chronological_order(self):
        """Test that list_agent_runs returns runtimes in chronological order"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            agent_id = "test-agent-chronological"

            # Create a session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Create multiple runtimes with different timestamps
            # Note: id is a timestamp string, so we create them with explicit values
            runtime1 = AgentRun(
                agent_id=agent_id,
                id="1000.0",  # Earliest
                status=AgentRunStatus.COMPLETED,
            )
            runtime2 = AgentRun(
                agent_id=agent_id,
                id="2000.0",  # Middle
                status=AgentRunStatus.COMPLETED,
            )
            runtime3 = AgentRun(
                agent_id=agent_id,
                id="3000.0",  # Latest
                status=AgentRunStatus.COMPLETED,
            )

            # Save in random order using session_id
            repo.update_agent_run(session.id, runtime2)
            repo.update_agent_run(session.id, runtime1)
            repo.update_agent_run(session.id, runtime3)

            # List runtimes using session_id
            runtimes = repo.list_agent_runs(session.id)

            # Verify we got all 3
            assert len(runtimes) == 3

            # Verify they are in chronological order (increasing id)
            assert runtimes[0].id == "1000.0"
            assert runtimes[1].id == "2000.0"
            assert runtimes[2].id == "3000.0"

            # Verify the order is maintained
            for i in range(len(runtimes) - 1):
                assert runtimes[i].id < runtimes[i + 1].id

    def test_update_and_get_agent_session(self):
        """Test creating and retrieving agent session metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id="test-agent-meta-123",
                description="A test agent for testing purposes",
            )

            # Save agent metadata
            repo.update_agent_run_session(agent_meta)

            # Verify agent file exists in the new structure
            session_file = repo._get_session_file(agent_meta.id)
            assert session_file.exists()

            # Retrieve agent metadata using session ID
            retrieved_agent = repo.get_agent_run_session(agent_meta.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "test-agent-meta-123"
            assert retrieved_agent.description == "A test agent for testing purposes"

    def test_get_nonexistent_agent_session(self):
        """Test retrieving agent session that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent agent using a fake session ID
            agent = repo.get_agent_run_session("nonexistent-session-id-12345")
            assert agent is None

    def test_update_existing_agent_session(self):
        """Test updating existing agent session metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id="test-agent-update-meta",
                description="Initial description",
            )
            repo.update_agent_run_session(agent_meta)

            # Update agent metadata
            agent_meta.description = "Updated description"
            repo.update_agent_run_session(agent_meta)

            # Retrieve and verify using session ID
            retrieved_agent = repo.get_agent_run_session(agent_meta.id)
            assert retrieved_agent.description == "Updated description"

    def test_list_agents_empty(self):
        """Test listing agents when repository is empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # List agents in empty repository
            agents = repo.list_agent_run_sessions()
            assert agents == []

    def test_list_agents_multiple(self):
        """Test listing multiple agents"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create multiple agents
            agent1 = AgentRunSession(
                agent_id="agent-001",
                description="Agent 1",
            )
            agent2 = AgentRunSession(
                agent_id="agent-002",
                description="Agent 2",
            )
            agent3 = AgentRunSession(
                agent_id="agent-003",
                description="Agent 3",
            )

            # Save in random order
            repo.update_agent_run_session(agent2)
            repo.update_agent_run_session(agent1)
            repo.update_agent_run_session(agent3)

            # List agents
            agents = repo.list_agent_run_sessions()

            # Verify we got all 3
            assert len(agents) == 3

            # Verify they are sorted by agent_id
            assert agents[0].agent_id == "agent-001"
            assert agents[1].agent_id == "agent-002"
            assert agents[2].agent_id == "agent-003"

            # Verify descriptions
            assert agents[0].description == "Agent 1"
            assert agents[1].description == "Agent 2"
            assert agents[2].description == "Agent 3"

    def test_delete_agent_session(self):
        """Test deleting an agent session and all its runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            agent_id = "test-agent-delete"

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id=agent_id,
            )
            repo.update_agent_run_session(agent_meta)

            # Create multiple runtimes for this agent
            runtime1 = AgentRun(
                agent_id=agent_id,
                id="1000.0",
            )
            runtime2 = AgentRun(
                agent_id=agent_id,
                id="2000.0",
            )
            repo.update_agent_run(agent_meta.id, runtime1)
            repo.update_agent_run(agent_meta.id, runtime2)

            # Verify agent and runtimes exist
            agent = repo.get_agent_run_session(agent_meta.id)
            assert agent is not None
            session_dir = repo._get_session_dir(agent.id)
            assert session_dir.exists()
            assert len(repo.list_agent_runs(agent.id)) == 2

            # Delete agent using session ID
            repo.delete_agent_run_session(agent_meta.id)

            # Verify agent and all runtimes are deleted
            assert repo.get_agent_run_session(agent_meta.id) is None
            assert len(repo.list_agent_runs(agent.id)) == 0
            assert not session_dir.exists()

    def test_delete_nonexistent_agent_session(self):
        """Test deleting an agent session that doesn't exist (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Delete non-existent agent (should not raise error)
            repo.delete_agent_run_session("nonexistent-session-id-12345")

            # Verify nothing broke
            assert repo.get_agent_run_session("nonexistent-session-id-12345") is None

    def test_agent_session_with_minimal_fields(self):
        """Test agent session with only required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata with only agent_id
            agent_meta = AgentRunSession(agent_id="minimal-agent")
            repo.update_agent_run_session(agent_meta)

            # Retrieve and verify using session ID
            retrieved_agent = repo.get_agent_run_session(agent_meta.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "minimal-agent"
            assert retrieved_agent.description is None

    def test_agent_storage_structure(self):
        """Test that agent metadata storage structure matches expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id="structure-test-agent",
                description="Test agent",
            )
            repo.update_agent_run_session(agent_meta)

            # Verify directory structure
            session_dir = repo._get_session_dir(agent_meta.id)
            assert session_dir.exists()
            session_file = repo._get_session_file(agent_meta.id)
            assert session_file.exists()

            # Verify session.json is valid JSON
            import json

            with open(session_file, "r") as f:
                data = json.load(f)
                assert data["agent_id"] == "structure-test-agent"
                assert data["description"] == "Test agent"

    def test_delete_agent_with_tool_calls_in_runtimes(self):
        """Test deleting an agent that has runtimes with tool calls"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            agent_id = "agent-with-complex-data"

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id=agent_id,
                description="Complex agent",
            )
            repo.update_agent_run_session(agent_meta)

            # Create runtime with embedded tool calls
            runtime = AgentRun(
                agent_id=agent_id,
            )

            # Add tool calls to runtime
            tool_call1 = AgentRunToolCall(id="tool-1", tool_id="Tool1")
            tool_call2 = AgentRunToolCall(id="tool-2", tool_id="Tool2")
            runtime.tool_calls["tool-1"] = tool_call1
            runtime.tool_calls["tool-2"] = tool_call2

            repo.update_agent_run(agent_meta.id, runtime)

            # Verify everything exists
            assert repo.get_agent_run_session(agent_meta.id) is not None
            retrieved_runtime = repo.get_agent_run(agent_meta.id, runtime.id)
            assert retrieved_runtime is not None
            assert len(retrieved_runtime.tool_calls) == 2

            # Delete agent (should delete everything)
            repo.delete_agent_run_session(agent_meta.id)

            # Verify everything is deleted
            assert repo.get_agent_run_session(agent_meta.id) is None
            assert repo.get_agent_run(agent_meta.id, runtime.id) is None

    def test_list_agents_after_deletion(self):
        """Test that deleted agents don't appear in list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create multiple agents
            agent1 = AgentRunSession(agent_id="agent-keep-1")
            agent2 = AgentRunSession(agent_id="agent-delete")
            agent3 = AgentRunSession(agent_id="agent-keep-2")

            repo.update_agent_run_session(agent1)
            repo.update_agent_run_session(agent2)
            repo.update_agent_run_session(agent3)

            # Verify all 3 exist
            assert len(repo.list_agent_run_sessions()) == 3

            # Delete one agent using session ID
            repo.delete_agent_run_session(agent2.id)

            # Verify only 2 remain
            agents = repo.list_agent_run_sessions()
            assert len(agents) == 2
            agent_ids = {a.agent_id for a in agents}
            assert "agent-keep-1" in agent_ids
            assert "agent-keep-2" in agent_ids
            assert "agent-delete" not in agent_ids
