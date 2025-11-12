#!/usr/bin/env python3
"""
Integration tests for FileTaskRuntimeRepository with TaskMonitor.
"""

import tempfile
from datetime import datetime

from fivcplayground.tasks.types import (
    TaskMonitor,
    TaskRuntime,
    TaskRuntimeStep,
    TaskStatus,
)
from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
from fivcplayground.utils import OutputDir


class TestRepositoryIntegration:
    """Integration tests for repository with TaskMonitor"""

    def test_task_monitor_with_repository(self):
        """Test TaskMonitor with FileTaskRuntimeRepository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a TaskMonitor with repository
            monitor = TaskMonitor(runtime_repo=repo)

            # Verify task is persisted
            task_id = monitor.id
            persisted_task = repo.get_task_runtime(task_id)
            assert persisted_task is not None
            assert persisted_task.id == task_id

    def test_task_monitor_persist_steps(self):
        """Test TaskMonitor persisting steps through repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a TaskMonitor with repository
            monitor = TaskMonitor(runtime_repo=repo)
            task_id = monitor.id

            # Manually add a step (simulating what would happen during execution)
            step = TaskRuntimeStep(
                id="agent-1",
                agent_name="TestAgent",
                status=TaskStatus.EXECUTING,
                started_at=datetime.now(),
            )
            monitor.steps[step.id] = step

            # Persist the step
            repo.update_task_runtime_step(task_id, step)

            # Verify step is persisted
            persisted_step = repo.get_task_runtime_step(task_id, "agent-1")
            assert persisted_step is not None
            assert persisted_step.id == "agent-1"
            assert persisted_step.agent_name == "TestAgent"

    def test_task_monitor_reload_from_repository(self):
        """Test reloading TaskMonitor state from repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create and persist a task with steps
            task = TaskRuntime(
                id="test-task-reload",
                status=TaskStatus.EXECUTING,
                started_at=datetime.now(),
            )
            repo.update_task_runtime(task)

            step1 = TaskRuntimeStep(
                id="agent-1",
                agent_name="Agent1",
                status=TaskStatus.COMPLETED,
            )
            step2 = TaskRuntimeStep(
                id="agent-2",
                agent_name="Agent2",
                status=TaskStatus.EXECUTING,
            )
            repo.update_task_runtime_step("test-task-reload", step1)
            repo.update_task_runtime_step("test-task-reload", step2)

            # Create a new TaskMonitor with the persisted runtime
            persisted_task = repo.get_task_runtime("test-task-reload")
            monitor = TaskMonitor(runtime=persisted_task, runtime_repo=repo)

            # Verify steps are loaded
            steps = monitor.list_steps()
            assert len(steps) == 2

            step_ids = {step.id for step in steps}
            assert "agent-1" in step_ids
            assert "agent-2" in step_ids

    def test_task_monitor_cleanup_with_repository(self):
        """Test TaskMonitor cleanup removes data from repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a TaskMonitor with repository
            monitor = TaskMonitor(runtime_repo=repo)
            task_id = monitor.id

            # Add a step
            step = TaskRuntimeStep(
                id="agent-1",
                agent_name="TestAgent",
            )
            monitor.steps[step.id] = step
            repo.update_task_runtime_step(task_id, step)

            # Verify task and step exist
            assert repo.get_task_runtime(task_id) is not None
            assert repo.get_task_runtime_step(task_id, "agent-1") is not None

            # Cleanup
            monitor.cleanup()

            # Verify task and steps are deleted
            assert repo.get_task_runtime(task_id) is None
            assert repo.get_task_runtime_step(task_id, "agent-1") is None

    def test_multiple_tasks_in_repository(self):
        """Test managing multiple tasks in repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create multiple monitors
            monitor1 = TaskMonitor(runtime_repo=repo)
            monitor2 = TaskMonitor(runtime_repo=repo)
            monitor3 = TaskMonitor(runtime_repo=repo)

            # List all tasks
            tasks = repo.list_task_runtimes()
            assert len(tasks) == 3

            task_ids = {task.id for task in tasks}
            assert monitor1.id in task_ids
            assert monitor2.id in task_ids
            assert monitor3.id in task_ids

    def test_task_monitor_persist_method(self):
        """Test TaskMonitor.persist() method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a TaskMonitor with repository
            monitor = TaskMonitor(runtime_repo=repo)
            task_id = monitor.id

            # Add steps
            step1 = TaskRuntimeStep(
                id="agent-1",
                agent_name="Agent1",
                status=TaskStatus.COMPLETED,
            )
            step2 = TaskRuntimeStep(
                id="agent-2",
                agent_name="Agent2",
                status=TaskStatus.EXECUTING,
            )
            monitor.steps[step1.id] = step1
            monitor.steps[step2.id] = step2

            # Persist all data
            monitor.persist()

            # Verify all data is persisted
            persisted_task = repo.get_task_runtime(task_id)
            assert persisted_task is not None

            persisted_steps = repo.list_task_runtime_steps(task_id)
            assert len(persisted_steps) == 2

            step_ids = {step.id for step in persisted_steps}
            assert "agent-1" in step_ids
            assert "agent-2" in step_ids
