#!/usr/bin/env python3
"""
Tests for FileAgentRunRepository functionality.
"""

import pytest
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

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    @pytest.mark.asyncio
    async def test_update_and_get_agent(self):
        """Test creating and retrieving an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-123")
            await repo.update_agent_run_session_async(session)

            # Create an agent runtime
            agent = AgentRun(
                agent_id="test-agent-123",
                status=AgentRunStatus.EXECUTING,
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            # Save agent using session_id
            await repo.update_agent_run_async(session.id, agent)

            # Verify agent file exists in the new structure
            agent_file = repo._get_run_file(session.id, agent.id)
            assert agent_file.exists()

            # Retrieve agent runtime using session_id
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "test-agent-123"
            assert retrieved_agent.status == AgentRunStatus.EXECUTING
            assert retrieved_agent.started_at == datetime(2024, 1, 1, 12, 0, 0)

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self):
        """Test retrieving an agent that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent agent using a fake session_id
            agent = await repo.get_agent_run_async(
                "nonexistent-session-id", "nonexistent-run"
            )
            assert agent is None

    @pytest.mark.asyncio
    async def test_delete_agent(self):
        """Test deleting an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-456")
            await repo.update_agent_run_session_async(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-456",
            )
            await repo.update_agent_run_async(session.id, agent)

            # Verify agent exists
            assert await repo.get_agent_run_async(session.id, agent.id) is not None

            # Verify file path
            run_file = repo._get_run_file(session.id, agent.id)
            assert run_file.exists()

            # Delete agent runtime using session_id
            await repo.delete_agent_run_async(session.id, agent.id)

            # Verify agent is deleted
            assert await repo.get_agent_run_async(session.id, agent.id) is None
            assert not run_file.exists()

    @pytest.mark.asyncio
    async def test_update_and_get_tool_call(self):
        """Test creating and retrieving a tool call (embedded in runtime)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-789")
            await repo.update_agent_run_session_async(session)

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
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve agent runtime using session_id
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved_agent is not None
            assert "tool-call-1" in retrieved_agent.tool_calls

            # Verify tool call data
            retrieved_tool_call = retrieved_agent.tool_calls["tool-call-1"]
            assert retrieved_tool_call.id == "tool-call-1"
            assert retrieved_tool_call.tool_id == "TestTool"
            assert retrieved_tool_call.tool_input == {"param": "value"}
            assert retrieved_tool_call.status == "pending"

    @pytest.mark.asyncio
    async def test_get_nonexistent_tool_call(self):
        """Test retrieving a tool call that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent runtime (which would have no tool calls)
            runtime = await repo.get_agent_run_async(
                "nonexistent-session-id", "nonexistent-run"
            )
            assert runtime is None

    @pytest.mark.asyncio
    async def test_list_tool_calls(self):
        """Test listing all tool calls for an agent runtime (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-999")
            await repo.update_agent_run_session_async(session)

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
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify tool calls using session_id
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert len(retrieved_agent.tool_calls) == 3

            tool_call_ids = set(retrieved_agent.tool_calls.keys())
            assert "tool-call-1" in tool_call_ids
            assert "tool-call-2" in tool_call_ids
            assert "tool-call-3" in tool_call_ids

    @pytest.mark.asyncio
    async def test_list_tool_calls_for_nonexistent_agent(self):
        """Test retrieving runtime for an agent that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Get runtime for non-existent session
            runtime = await repo.get_agent_run_async(
                "nonexistent-session-id", "nonexistent-run"
            )
            assert runtime is None

    @pytest.mark.asyncio
    async def test_update_existing_agent(self):
        """Test updating an existing agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-update")
            await repo.update_agent_run_session_async(session)

            # Create an agent
            agent = AgentRun(
                agent_id="test-agent-update",
                status=AgentRunStatus.PENDING,
            )
            await repo.update_agent_run_async(session.id, agent)

            # Update agent status
            agent.status = AgentRunStatus.COMPLETED
            agent.completed_at = datetime(2024, 1, 1, 13, 0, 0)
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved_agent.status == AgentRunStatus.COMPLETED
            assert retrieved_agent.completed_at == datetime(2024, 1, 1, 13, 0, 0)

    @pytest.mark.asyncio
    async def test_update_existing_tool_call(self):
        """Test updating an existing tool call (embedded in runtime)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-tool-update")
            await repo.update_agent_run_session_async(session)

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
            await repo.update_agent_run_async(session.id, agent)

            # Update tool call
            tool_call.status = "success"
            tool_call.completed_at = datetime(2024, 1, 1, 14, 0, 0)
            tool_call.tool_result = {"result": "success"}
            agent.tool_calls["tool-call-update"] = tool_call
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            retrieved_tool_call = retrieved_agent.tool_calls["tool-call-update"]
            assert retrieved_tool_call.status == "success"
            assert retrieved_tool_call.completed_at == datetime(2024, 1, 1, 14, 0, 0)
            assert retrieved_tool_call.tool_result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_delete_agent_with_tool_calls(self):
        """Test deleting an agent that has tool calls (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="test-agent-with-tools")
            await repo.update_agent_run_session_async(session)

            # Create an agent with embedded tool calls
            agent = AgentRun(
                agent_id="test-agent-with-tools",
            )

            tool_call1 = AgentRunToolCall(id="tool-1", tool_id="Tool1")
            tool_call2 = AgentRunToolCall(id="tool-2", tool_id="Tool2")
            agent.tool_calls["tool-1"] = tool_call1
            agent.tool_calls["tool-2"] = tool_call2

            await repo.update_agent_run_async(session.id, agent)

            # Verify agent and tool calls exist
            retrieved = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved is not None
            assert len(retrieved.tool_calls) == 2

            # Delete agent runtime
            await repo.delete_agent_run_async(session.id, agent.id)

            # Verify agent and tool calls are deleted
            assert await repo.get_agent_run_async(session.id, agent.id) is None

    @pytest.mark.asyncio
    async def test_storage_structure(self):
        """Test that the storage structure matches the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="structure-test")
            await repo.update_agent_run_session_async(session)

            # Create an agent with embedded tool calls
            agent = AgentRun(
                agent_id="structure-test",
            )

            tool_call = AgentRunToolCall(id="tool-1", tool_id="TestTool")
            agent.tool_calls["tool-1"] = tool_call

            await repo.update_agent_run_async(session.id, agent)

            # Verify new directory structure: session_<id>/run_<id>.json
            session_dir = repo._get_session_dir(session.id)
            assert session_dir.exists()

            run_file = repo._get_run_file(session.id, agent.id)
            assert run_file.exists()
            assert run_file.name == f"run_{agent.id}.json"

    @pytest.mark.asyncio
    async def test_agent_with_streaming_text(self):
        """Test agent runtime with streaming text - verify it's excluded from persistence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="streaming-agent")
            await repo.update_agent_run_session_async(session)

            # Create an agent with streaming text
            agent = AgentRun(
                agent_id="streaming-agent",
                streaming_text="This is streaming text...",
            )
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify
            # streaming_text is excluded from serialization, so it should be empty string (default)
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved_agent.streaming_text == ""

    @pytest.mark.asyncio
    async def test_agent_with_error(self):
        """Test agent runtime with error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="error-agent")
            await repo.update_agent_run_session_async(session)

            # Create an agent with error
            agent = AgentRun(
                agent_id="error-agent",
                status=AgentRunStatus.FAILED,
                error="Something went wrong",
            )
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
            assert retrieved_agent.status == AgentRunStatus.FAILED
            assert retrieved_agent.error == "Something went wrong"

    @pytest.mark.asyncio
    async def test_tool_call_with_complex_input_and_result(self):
        """Test tool call with complex input and result data (embedded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create a session first
            session = AgentRunSession(agent_id="complex-agent")
            await repo.update_agent_run_session_async(session)

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
            await repo.update_agent_run_async(session.id, agent)

            # Retrieve and verify
            retrieved_agent = await repo.get_agent_run_async(session.id, agent.id)
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

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self):
        """Test deleting an agent that doesn't exist (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Delete non-existent agent (should not raise error)
            await repo.delete_agent_run_async(
                "nonexistent-session-id", "nonexistent-run"
            )

            # Verify nothing broke
            assert (
                await repo.get_agent_run_async(
                    "nonexistent-session-id", "nonexistent-run"
                )
                is None
            )

    @pytest.mark.asyncio
    async def test_list_agent_runtimes_chronological_order(self):
        """Test that list_agent_runs returns runtimes in chronological order"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            agent_id = "test-agent-chronological"

            # Create a session first
            session = AgentRunSession(agent_id=agent_id)
            await repo.update_agent_run_session_async(session)

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
            await repo.update_agent_run_async(session.id, runtime2)
            await repo.update_agent_run_async(session.id, runtime1)
            await repo.update_agent_run_async(session.id, runtime3)

            # List runtimes using session_id
            runtimes = await repo.list_agent_runs_async(session.id)

            # Verify we got all 3
            assert len(runtimes) == 3

            # Verify they are in chronological order (increasing id)
            assert runtimes[0].id == "1000.0"
            assert runtimes[1].id == "2000.0"
            assert runtimes[2].id == "3000.0"

            # Verify the order is maintained
            for i in range(len(runtimes) - 1):
                assert runtimes[i].id < runtimes[i + 1].id

    @pytest.mark.asyncio
    async def test_update_and_get_agent_session(self):
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
            await repo.update_agent_run_session_async(agent_meta)

            # Verify agent file exists in the new structure
            session_file = repo._get_session_file(agent_meta.id)
            assert session_file.exists()

            # Retrieve agent metadata using session ID
            retrieved_agent = await repo.get_agent_run_session_async(agent_meta.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "test-agent-meta-123"
            assert retrieved_agent.description == "A test agent for testing purposes"

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_session(self):
        """Test retrieving agent session that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Try to get non-existent agent using a fake session ID
            agent = await repo.get_agent_run_session_async(
                "nonexistent-session-id-12345"
            )
            assert agent is None

    @pytest.mark.asyncio
    async def test_update_existing_agent_session(self):
        """Test updating existing agent session metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id="test-agent-update-meta",
                description="Initial description",
            )
            await repo.update_agent_run_session_async(agent_meta)

            # Update agent metadata
            agent_meta.description = "Updated description"
            await repo.update_agent_run_session_async(agent_meta)

            # Retrieve and verify using session ID
            retrieved_agent = await repo.get_agent_run_session_async(agent_meta.id)
            assert retrieved_agent.description == "Updated description"

    @pytest.mark.asyncio
    async def test_list_agents_empty(self):
        """Test listing agents when repository is empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # List agents in empty repository
            agents = await repo.list_agent_run_sessions_async()
            assert agents == []

    @pytest.mark.asyncio
    async def test_list_agents_multiple(self):
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
            await repo.update_agent_run_session_async(agent2)
            await repo.update_agent_run_session_async(agent1)
            await repo.update_agent_run_session_async(agent3)

            # List agents
            agents = await repo.list_agent_run_sessions_async()

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

    @pytest.mark.asyncio
    async def test_delete_agent_session(self):
        """Test deleting an agent session and all its runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            agent_id = "test-agent-delete"

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id=agent_id,
            )
            await repo.update_agent_run_session_async(agent_meta)

            # Create multiple runtimes for this agent
            runtime1 = AgentRun(
                agent_id=agent_id,
                id="1000.0",
            )
            runtime2 = AgentRun(
                agent_id=agent_id,
                id="2000.0",
            )
            await repo.update_agent_run_async(agent_meta.id, runtime1)
            await repo.update_agent_run_async(agent_meta.id, runtime2)

            # Verify agent and runtimes exist
            agent = await repo.get_agent_run_session_async(agent_meta.id)
            assert agent is not None
            session_dir = repo._get_session_dir(agent.id)
            assert session_dir.exists()
            assert len(await repo.list_agent_runs_async(agent.id)) == 2

            # Delete agent using session ID
            await repo.delete_agent_run_session_async(agent_meta.id)

            # Verify agent and all runtimes are deleted
            assert await repo.get_agent_run_session_async(agent_meta.id) is None
            assert len(await repo.list_agent_runs_async(agent.id)) == 0
            assert not session_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent_session(self):
        """Test deleting an agent session that doesn't exist (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Delete non-existent agent (should not raise error)
            await repo.delete_agent_run_session_async("nonexistent-session-id-12345")

            # Verify nothing broke
            assert (
                await repo.get_agent_run_session_async("nonexistent-session-id-12345")
                is None
            )

    @pytest.mark.asyncio
    async def test_agent_session_with_minimal_fields(self):
        """Test agent session with only required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata with only agent_id
            agent_meta = AgentRunSession(agent_id="minimal-agent")
            await repo.update_agent_run_session_async(agent_meta)

            # Retrieve and verify using session ID
            retrieved_agent = await repo.get_agent_run_session_async(agent_meta.id)
            assert retrieved_agent is not None
            assert retrieved_agent.agent_id == "minimal-agent"
            assert retrieved_agent.description is None

    @pytest.mark.asyncio
    async def test_agent_storage_structure(self):
        """Test that agent metadata storage structure matches expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create agent metadata
            agent_meta = AgentRunSession(
                agent_id="structure-test-agent",
                description="Test agent",
            )
            await repo.update_agent_run_session_async(agent_meta)

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

    @pytest.mark.asyncio
    async def test_delete_agent_with_tool_calls_in_runtimes(self):
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
            await repo.update_agent_run_session_async(agent_meta)

            # Create runtime with embedded tool calls
            runtime = AgentRun(
                agent_id=agent_id,
            )

            # Add tool calls to runtime
            tool_call1 = AgentRunToolCall(id="tool-1", tool_id="Tool1")
            tool_call2 = AgentRunToolCall(id="tool-2", tool_id="Tool2")
            runtime.tool_calls["tool-1"] = tool_call1
            runtime.tool_calls["tool-2"] = tool_call2

            await repo.update_agent_run_async(agent_meta.id, runtime)

            # Verify everything exists
            assert await repo.get_agent_run_session_async(agent_meta.id) is not None
            retrieved_runtime = await repo.get_agent_run_async(
                agent_meta.id, runtime.id
            )
            assert retrieved_runtime is not None
            assert len(retrieved_runtime.tool_calls) == 2

            # Delete agent (should delete everything)
            await repo.delete_agent_run_session_async(agent_meta.id)

            # Verify everything is deleted
            assert await repo.get_agent_run_session_async(agent_meta.id) is None
            assert await repo.get_agent_run_async(agent_meta.id, runtime.id) is None

    @pytest.mark.asyncio
    async def test_list_agents_after_deletion(self):
        """Test that deleted agents don't appear in list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create multiple agents
            agent1 = AgentRunSession(agent_id="agent-keep-1")
            agent2 = AgentRunSession(agent_id="agent-delete")
            agent3 = AgentRunSession(agent_id="agent-keep-2")

            await repo.update_agent_run_session_async(agent1)
            await repo.update_agent_run_session_async(agent2)
            await repo.update_agent_run_session_async(agent3)

            # Verify all 3 exist
            assert len(await repo.list_agent_run_sessions_async()) == 3

            # Delete one agent using session ID
            await repo.delete_agent_run_session_async(agent2.id)

            # Verify only 2 remain
            agents = await repo.list_agent_run_sessions_async()
            assert len(agents) == 2
            agent_ids = {a.agent_id for a in agents}
            assert "agent-keep-1" in agent_ids
            assert "agent-keep-2" in agent_ids
            assert "agent-delete" not in agent_ids
