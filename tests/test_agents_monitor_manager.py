#!/usr/bin/env python3
"""
Tests for AgentMonitorManager functionality.
"""

import tempfile
from unittest.mock import Mock

from fivcplayground.agents.types import (
    AgentMonitorManager,
    AgentMonitor,
    AgentRunToolCall,
    AgentRunStatus,
    AgentRunSession,
)
from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
from fivcplayground.utils import OutputDir


class TestAgentsMonitorManager:
    """Tests for AgentMonitorManager class"""

    def test_initialization(self):
        """Test AgentMonitorManager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            manager = AgentMonitorManager(runtime_repo=repo)

            # Manager should have a repository
            assert manager._repo is not None
            assert isinstance(manager._repo, FileAgentRunRepository)

    def test_create_agent_runtime(self):
        """Test creating an agent runtime monitor (current incomplete implementation)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            manager = AgentMonitorManager(runtime_repo=repo)

            # Current implementation only accepts on_event parameter
            monitor = manager.create_agent_runtime(on_event=None)

            # Verify monitor was created
            assert monitor is not None
            assert isinstance(monitor, AgentMonitor)
            assert monitor._repo is not None

            # Note: Full implementation should accept query, agent_id, tool_retriever,
            # and agent_creator parameters and return the created agent instance.
            # See REFACTORING_ISSUES.md for details on what needs to be implemented.

    def test_create_agent_runtime_with_callback(self):
        """Test creating an agent runtime with event callback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            manager = AgentMonitorManager(runtime_repo=repo)

            # Current implementation accepts on_event parameter
            callback = Mock()
            monitor = manager.create_agent_runtime(on_event=callback)

            # Verify callback was passed to monitor
            assert monitor is not None
            assert isinstance(monitor, AgentMonitor)
            assert monitor._on_event == callback

    def test_create_agent_runtime_returns_monitor(self):
        """Test that create_agent_runtime returns AgentMonitor instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            manager = AgentMonitorManager(runtime_repo=repo)

            # Current implementation returns AgentMonitor
            monitor = manager.create_agent_runtime()

            # Verify monitor was created
            assert monitor is not None
            assert isinstance(monitor, AgentMonitor)
            assert monitor._repo is repo

            # Verify monitor has a runtime with auto-generated IDs
            assert monitor._runtime is not None
            assert monitor._runtime.id is not None
            assert len(monitor._runtime.id) > 0

    def test_list_agent_runtimes(self):
        """Test listing agent runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)
            manager = AgentMonitorManager(runtime_repo=repo)

            # Create multiple monitors manually
            agent_id = "test-agent-123"

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Create first monitor
            monitor1 = manager.create_agent_runtime()
            runtime1 = monitor1._runtime
            runtime1.agent_id = agent_id
            repo.update_agent_run(session.id, runtime1)

            # Create second monitor
            monitor2 = manager.create_agent_runtime()
            runtime2 = monitor2._runtime
            runtime2.agent_id = agent_id
            repo.update_agent_run(session.id, runtime2)

            monitors = manager.list_agent_runtimes(agent_id)
            assert len(monitors) == 2

            # Verify both agent runtimes are in the list
            assert all(isinstance(m, AgentMonitor) for m in monitors)

    def test_list_agent_runtimes_empty(self):
        """Test listing agent runtimes when repository is empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            agents = manager.list_agent_runtimes("nonexistent-agent")
            assert agents == []

    def test_list_agent_runtimes_with_status_filter(self):
        """Test listing agent runtimes filtered by status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Use same agent_id for all runtimes
            agent_id = "test-agent-123"

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Create monitors and manually set their statuses
            monitor1 = manager.create_agent_runtime()
            runtime1 = monitor1._runtime
            runtime1.agent_id = agent_id
            runtime1.status = AgentRunStatus.PENDING
            repo.update_agent_run(session.id, runtime1)

            monitor2 = manager.create_agent_runtime()
            runtime2 = monitor2._runtime
            runtime2.agent_id = agent_id
            runtime2.status = AgentRunStatus.EXECUTING
            repo.update_agent_run(session.id, runtime2)

            monitor3 = manager.create_agent_runtime()
            runtime3 = monitor3._runtime
            runtime3.agent_id = agent_id
            runtime3.status = AgentRunStatus.COMPLETED
            repo.update_agent_run(session.id, runtime3)

            # Filter by EXECUTING status
            executing_agents = manager.list_agent_runtimes(
                agent_id, status=[AgentRunStatus.EXECUTING]
            )
            assert len(executing_agents) == 1
            assert executing_agents[0]._runtime.id == runtime2.id

            # Filter by multiple statuses
            pending_or_completed = manager.list_agent_runtimes(
                agent_id, status=[AgentRunStatus.PENDING, AgentRunStatus.COMPLETED]
            )
            assert len(pending_or_completed) == 2
            run_ids = {agent._runtime.id for agent in pending_or_completed}
            assert runtime1.id in run_ids
            assert runtime3.id in run_ids

    def test_get_agent_runtime(self):
        """Test getting a specific agent runtime monitor"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.id

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_run(session.id, runtime)

            result = manager.get_agent_runtime(agent_id, agent_run_id)
            assert result is not None
            assert isinstance(result, AgentMonitor)
            assert result._runtime.agent_id == agent_id

    def test_get_agent_runtime_nonexistent(self):
        """Test getting a nonexistent agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            result = manager.get_agent_runtime("nonexistent", "nonexistent-run")
            assert result is None

    def test_get_agent_runtime_with_callback(self):
        """Test getting an agent runtime monitor with event callback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.id

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_run(session.id, runtime)

            callback = Mock()
            result = manager.get_agent_runtime(
                agent_id, agent_run_id, on_event=callback
            )
            assert result is not None
            assert result._on_event == callback

    def test_delete_agent_runtime(self):
        """Test deleting an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.id

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_run(session.id, runtime)

            assert len(manager.list_agent_runtimes(agent_id)) == 1

            manager.delete_agent_runtime(agent_id, agent_run_id)

            assert len(manager.list_agent_runtimes(agent_id)) == 0

    def test_delete_agent_runtime_nonexistent(self):
        """Test deleting a nonexistent agent runtime (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Should not raise error
            manager.delete_agent_runtime("nonexistent", "nonexistent-run")

    def test_save_and_load(self):
        """Test saving and loading agent runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            # Create manager and add data
            manager = AgentMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.id

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Update runtime with agent_id and embedded tool call
            runtime = monitor._runtime
            runtime.agent_id = agent_id

            # Add a tool call to the runtime
            tool_call = AgentRunToolCall(
                id="tool-1",
                tool_name="calculator",
                tool_input={"expression": "2+2"},
                status="success",
            )
            runtime.tool_calls["tool-1"] = tool_call

            repo.update_agent_run(session.id, runtime)

            # Verify session directory was created
            session_dir = repo._get_session_dir(session.id)
            assert session_dir.exists()

            # Load in new manager with same repository
            manager2 = AgentMonitorManager(runtime_repo=repo)

            monitors = manager2.list_agent_runtimes(agent_id)
            assert len(monitors) == 1

            # Load the agent runtime monitor
            loaded_monitor = manager2.get_agent_runtime(agent_id, agent_run_id)
            assert loaded_monitor is not None

            # Load tool calls from the runtime
            loaded_runtime = repo.get_agent_run(session.id, agent_run_id)
            assert len(loaded_runtime.tool_calls) == 1
            assert loaded_runtime.tool_calls["tool-1"].tool_name == "calculator"

    def test_list_tool_calls(self):
        """Test listing tool calls for an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentRunRepository(output_dir=output_dir)

            manager = AgentMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.id

            # Create session first
            session = AgentRunSession(agent_id=agent_id)
            repo.update_agent_run_session(session)

            # Update runtime with agent_id and embedded tool calls
            runtime = monitor._runtime
            runtime.agent_id = agent_id

            # Add some tool calls (embedded)
            tool_call1 = AgentRunToolCall(id="tool-1", tool_name="calculator")
            tool_call2 = AgentRunToolCall(id="tool-2", tool_name="search")
            runtime.tool_calls["tool-1"] = tool_call1
            runtime.tool_calls["tool-2"] = tool_call2

            repo.update_agent_run(session.id, runtime)

            # Get agent runtime monitor and verify tool calls
            monitor = manager.get_agent_runtime(agent_id, agent_run_id)
            assert monitor is not None

            # Tool calls are now embedded in the runtime
            tool_calls = list(monitor._runtime.tool_calls.values())
            assert len(tool_calls) == 2

            tool_call_ids = {tc.id for tc in tool_calls}
            assert "tool-1" in tool_call_ids
            assert "tool-2" in tool_call_ids
