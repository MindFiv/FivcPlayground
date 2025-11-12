#!/usr/bin/env python3
"""
Tests for AgentsMonitorManager functionality.
"""

import os
import tempfile
from unittest.mock import Mock

from fivcplayground.agents.types import (
    AgentsMonitorManager,
    AgentsMonitor,
    AgentsRuntimeToolCall,
    AgentsStatus,
)
from fivcplayground.agents.types.repositories.files import FileAgentsRuntimeRepository
from fivcplayground.utils import OutputDir


class TestAgentsMonitorManager:
    """Tests for AgentsMonitorManager class"""

    def test_initialization(self):
        """Test AgentsMonitorManager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Manager should have a repository
            assert manager._repo is not None
            assert isinstance(manager._repo, FileAgentsRuntimeRepository)

    def test_create_agent_runtime(self):
        """Test creating an agent runtime monitor (current incomplete implementation)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Current implementation only accepts on_event parameter
            monitor = manager.create_agent_runtime(on_event=None)

            # Verify monitor was created
            assert monitor is not None
            assert isinstance(monitor, AgentsMonitor)
            assert monitor._repo is not None

            # Note: Full implementation should accept query, agent_id, tools_retriever,
            # and agent_creator parameters and return the created agent instance.
            # See REFACTORING_ISSUES.md for details on what needs to be implemented.

    def test_create_agent_runtime_with_callback(self):
        """Test creating an agent runtime with event callback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Current implementation accepts on_event parameter
            callback = Mock()
            monitor = manager.create_agent_runtime(on_event=callback)

            # Verify callback was passed to monitor
            assert monitor is not None
            assert isinstance(monitor, AgentsMonitor)
            assert monitor._on_event == callback

    def test_create_agent_runtime_returns_monitor(self):
        """Test that create_agent_runtime returns AgentsMonitor instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Current implementation returns AgentsMonitor
            monitor = manager.create_agent_runtime()

            # Verify monitor was created
            assert monitor is not None
            assert isinstance(monitor, AgentsMonitor)
            assert monitor._repo is repo

            # Verify monitor has a runtime with auto-generated IDs
            assert monitor._runtime is not None
            assert monitor._runtime.agent_run_id is not None
            assert len(monitor._runtime.agent_run_id) > 0

    def test_list_agent_runtimes(self):
        """Test listing agent runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create multiple monitors manually
            agent_id = "test-agent-123"

            # Create first monitor
            monitor1 = manager.create_agent_runtime()
            runtime1 = monitor1._runtime
            runtime1.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime1)

            # Create second monitor
            monitor2 = manager.create_agent_runtime()
            runtime2 = monitor2._runtime
            runtime2.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime2)

            monitors = manager.list_agent_runtimes(agent_id)
            assert len(monitors) == 2

            # Verify both agent runtimes are in the list
            assert all(isinstance(m, AgentsMonitor) for m in monitors)

    def test_list_agent_runtimes_empty(self):
        """Test listing agent runtimes when repository is empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            agents = manager.list_agent_runtimes("nonexistent-agent")
            assert agents == []

    def test_list_agent_runtimes_with_status_filter(self):
        """Test listing agent runtimes filtered by status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Use same agent_id for all runtimes
            agent_id = "test-agent-123"

            # Create monitors and manually set their statuses
            monitor1 = manager.create_agent_runtime()
            runtime1 = monitor1._runtime
            runtime1.agent_id = agent_id
            runtime1.status = AgentsStatus.PENDING
            repo.update_agent_runtime(agent_id, runtime1)

            monitor2 = manager.create_agent_runtime()
            runtime2 = monitor2._runtime
            runtime2.agent_id = agent_id
            runtime2.status = AgentsStatus.EXECUTING
            repo.update_agent_runtime(agent_id, runtime2)

            monitor3 = manager.create_agent_runtime()
            runtime3 = monitor3._runtime
            runtime3.agent_id = agent_id
            runtime3.status = AgentsStatus.COMPLETED
            repo.update_agent_runtime(agent_id, runtime3)

            # Filter by EXECUTING status
            executing_agents = manager.list_agent_runtimes(
                agent_id, status=[AgentsStatus.EXECUTING]
            )
            assert len(executing_agents) == 1
            assert executing_agents[0]._runtime.agent_run_id == runtime2.agent_run_id

            # Filter by multiple statuses
            pending_or_completed = manager.list_agent_runtimes(
                agent_id, status=[AgentsStatus.PENDING, AgentsStatus.COMPLETED]
            )
            assert len(pending_or_completed) == 2
            run_ids = {agent._runtime.agent_run_id for agent in pending_or_completed}
            assert runtime1.agent_run_id in run_ids
            assert runtime3.agent_run_id in run_ids

    def test_get_agent_runtime(self):
        """Test getting a specific agent runtime monitor"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.agent_run_id

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime)

            result = manager.get_agent_runtime(agent_id, agent_run_id)
            assert result is not None
            assert isinstance(result, AgentsMonitor)
            assert result._runtime.agent_id == agent_id

    def test_get_agent_runtime_nonexistent(self):
        """Test getting a nonexistent agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            result = manager.get_agent_runtime("nonexistent", "nonexistent-run")
            assert result is None

    def test_get_agent_runtime_with_callback(self):
        """Test getting an agent runtime monitor with event callback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.agent_run_id

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime)

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
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.agent_run_id

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime)

            assert len(manager.list_agent_runtimes(agent_id)) == 1

            manager.delete_agent_runtime(agent_id, agent_run_id)

            assert len(manager.list_agent_runtimes(agent_id)) == 0

    def test_delete_agent_runtime_nonexistent(self):
        """Test deleting a nonexistent agent runtime (should not raise error)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Should not raise error
            manager.delete_agent_runtime("nonexistent", "nonexistent-run")

    def test_save_and_load(self):
        """Test saving and loading agent runtimes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            # Create manager and add data
            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.agent_run_id

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime)

            # Add a tool call directly to repository
            tool_call = AgentsRuntimeToolCall(
                tool_use_id="tool-1",
                tool_name="calculator",
                tool_input={"expression": "2+2"},
                status="success",
            )
            repo.update_agent_runtime_tool_call(agent_id, agent_run_id, tool_call)

            # Verify agent directory was created
            agent_dir = os.path.join(tmpdir, f"agent_{agent_id}")
            assert os.path.exists(agent_dir)

            # Load in new manager with same repository
            manager2 = AgentsMonitorManager(runtime_repo=repo)

            monitors = manager2.list_agent_runtimes(agent_id)
            assert len(monitors) == 1

            # Load the agent runtime monitor
            loaded_monitor = manager2.get_agent_runtime(agent_id, agent_run_id)
            assert loaded_monitor is not None

            # Load tool calls through the repository
            loaded_tool_calls = repo.list_agent_runtime_tool_calls(
                agent_id, agent_run_id
            )
            assert len(loaded_tool_calls) == 1
            assert loaded_tool_calls[0].tool_name == "calculator"

    def test_list_tool_calls(self):
        """Test listing tool calls for an agent runtime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentsRuntimeRepository(output_dir=output_dir)

            manager = AgentsMonitorManager(runtime_repo=repo)

            # Create a monitor
            monitor = manager.create_agent_runtime()
            agent_id = "test-agent-123"
            agent_run_id = monitor._runtime.agent_run_id

            # Update runtime with agent_id
            runtime = monitor._runtime
            runtime.agent_id = agent_id
            repo.update_agent_runtime(agent_id, runtime)

            # Add some tool calls
            tool_call1 = AgentsRuntimeToolCall(
                tool_use_id="tool-1", tool_name="calculator"
            )
            tool_call2 = AgentsRuntimeToolCall(tool_use_id="tool-2", tool_name="search")
            repo.update_agent_runtime_tool_call(agent_id, agent_run_id, tool_call1)
            repo.update_agent_runtime_tool_call(agent_id, agent_run_id, tool_call2)

            # Get agent runtime monitor and list tool calls through the repository
            monitor = manager.get_agent_runtime(agent_id, agent_run_id)
            assert monitor is not None

            tool_calls = repo.list_agent_runtime_tool_calls(agent_id, agent_run_id)
            assert len(tool_calls) == 2

            tool_call_ids = {tc.tool_use_id for tc in tool_calls}
            assert "tool-1" in tool_call_ids
            assert "tool-2" in tool_call_ids
