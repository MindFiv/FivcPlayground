#!/usr/bin/env python3
"""
Tests for FileTaskRuntimeRepository functionality.
"""

import tempfile
from datetime import datetime

from fivcplayground.tasks.types import TaskRun, TaskRunStage, TaskRunStatus
from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
from fivcplayground.utils import OutputDir


class TestFileTaskRuntimeRepository:
    """Tests for FileTaskRuntimeRepository class"""

    def test_initialization(self):
        """Test repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_update_and_get_task(self):
        """Test creating and retrieving a task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(
                id="test-task-123",
                status=TaskRunStatus.EXECUTING,
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            # Save task
            repo.update_task_runtime(task)

            # Verify task file exists
            task_file = repo._get_task_file("test-task-123")
            assert task_file.exists()

            # Retrieve task
            retrieved_task = repo.get_task_runtime("test-task-123")
            assert retrieved_task is not None
            assert retrieved_task.id == "test-task-123"
            assert retrieved_task.status == TaskRunStatus.EXECUTING
            assert retrieved_task.started_at == datetime(2024, 1, 1, 12, 0, 0)

    def test_get_nonexistent_task(self):
        """Test retrieving a task that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Try to get non-existent task
            task = repo.get_task_runtime("nonexistent-task")
            assert task is None

    def test_delete_task(self):
        """Test deleting a task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(id="test-task-456")
            repo.update_task_runtime(task)

            # Verify task exists
            assert repo.get_task_runtime("test-task-456") is not None

            # Delete task
            repo.delete_task_runtime("test-task-456")

            # Verify task is deleted
            assert repo.get_task_runtime("test-task-456") is None
            assert not repo._get_task_dir("test-task-456").exists()

    def test_list_tasks(self):
        """Test listing all tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create multiple tasks
            task1 = TaskRun(id="task-1", status=TaskRunStatus.PENDING)
            task2 = TaskRun(id="task-2", status=TaskRunStatus.EXECUTING)
            task3 = TaskRun(id="task-3", status=TaskRunStatus.COMPLETED)

            repo.update_task_runtime(task1)
            repo.update_task_runtime(task2)
            repo.update_task_runtime(task3)

            # List tasks
            tasks = repo.list_task_runtimes()
            assert len(tasks) == 3

            task_ids = {task.id for task in tasks}
            assert "task-1" in task_ids
            assert "task-2" in task_ids
            assert "task-3" in task_ids

    def test_update_and_get_step(self):
        """Test creating and retrieving a step"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task first
            task = TaskRun(id="test-task-789")
            repo.update_task_runtime(task)

            # Create a step
            step = TaskRunStage(
                id="step-1",
                agent_name="TestAgent",
                status=TaskRunStatus.EXECUTING,
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            # Save step
            repo.update_task_runtime_step("test-task-789", step)

            # Verify step file exists
            step_file = repo._get_step_file("test-task-789", "step-1")
            assert step_file.exists()

            # Retrieve step
            retrieved_step = repo.get_task_runtime_step("test-task-789", "step-1")
            assert retrieved_step is not None
            assert retrieved_step.id == "step-1"
            assert retrieved_step.agent_name == "TestAgent"
            assert retrieved_step.status == TaskRunStatus.EXECUTING

    def test_get_nonexistent_step(self):
        """Test retrieving a step that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Try to get non-existent step
            step = repo.get_task_runtime_step("test-task-789", "nonexistent-step")
            assert step is None

    def test_list_steps(self):
        """Test listing all steps for a task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(id="test-task-999")
            repo.update_task_runtime(task)

            # Create multiple steps
            step1 = TaskRunStage(
                id="step-1",
                agent_name="Agent1",
                status=TaskRunStatus.PENDING,
            )
            step2 = TaskRunStage(
                id="step-2",
                agent_name="Agent2",
                status=TaskRunStatus.EXECUTING,
            )
            step3 = TaskRunStage(
                id="step-3",
                agent_name="Agent3",
                status=TaskRunStatus.COMPLETED,
            )

            repo.update_task_runtime_step("test-task-999", step1)
            repo.update_task_runtime_step("test-task-999", step2)
            repo.update_task_runtime_step("test-task-999", step3)

            # List steps
            steps = repo.list_task_runtime_steps("test-task-999")
            assert len(steps) == 3

            step_ids = {step.id for step in steps}
            assert "step-1" in step_ids
            assert "step-2" in step_ids
            assert "step-3" in step_ids

    def test_list_steps_for_nonexistent_task(self):
        """Test listing steps for a task that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # List steps for non-existent task
            steps = repo.list_task_runtime_steps("nonexistent-task")
            assert steps == []

    def test_update_existing_task(self):
        """Test updating an existing task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(
                id="test-task-update",
                status=TaskRunStatus.PENDING,
            )
            repo.update_task_runtime(task)

            # Update task status
            task.status = TaskRunStatus.COMPLETED
            task.completed_at = datetime(2024, 1, 1, 13, 0, 0)
            repo.update_task_runtime(task)

            # Retrieve and verify
            retrieved_task = repo.get_task_runtime("test-task-update")
            assert retrieved_task.status == TaskRunStatus.COMPLETED
            assert retrieved_task.completed_at == datetime(2024, 1, 1, 13, 0, 0)

    def test_update_existing_step(self):
        """Test updating an existing step"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(id="test-task-step-update")
            repo.update_task_runtime(task)

            # Create a step
            step = TaskRunStage(
                id="step-update",
                agent_name="TestAgent",
                status=TaskRunStatus.EXECUTING,
            )
            repo.update_task_runtime_step("test-task-step-update", step)

            # Update step
            step.status = TaskRunStatus.COMPLETED
            step.completed_at = datetime(2024, 1, 1, 14, 0, 0)
            repo.update_task_runtime_step("test-task-step-update", step)

            # Retrieve and verify
            retrieved_step = repo.get_task_runtime_step(
                "test-task-step-update", "step-update"
            )
            assert retrieved_step.status == TaskRunStatus.COMPLETED
            assert retrieved_step.completed_at == datetime(2024, 1, 1, 14, 0, 0)

    def test_delete_task_with_steps(self):
        """Test deleting a task that has steps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task with steps
            task = TaskRun(id="test-task-with-steps")
            repo.update_task_runtime(task)

            step1 = TaskRunStage(id="step-1", agent_name="Agent1")
            step2 = TaskRunStage(id="step-2", agent_name="Agent2")
            repo.update_task_runtime_step("test-task-with-steps", step1)
            repo.update_task_runtime_step("test-task-with-steps", step2)

            # Verify task and steps exist
            assert repo.get_task_runtime("test-task-with-steps") is not None
            assert len(repo.list_task_runtime_steps("test-task-with-steps")) == 2

            # Delete task
            repo.delete_task_runtime("test-task-with-steps")

            # Verify task and steps are deleted
            assert repo.get_task_runtime("test-task-with-steps") is None
            assert len(repo.list_task_runtime_steps("test-task-with-steps")) == 0

    def test_storage_structure(self):
        """Test that the storage structure matches the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)

            # Create a task with steps
            task = TaskRun(id="structure-test")
            repo.update_task_runtime(task)

            step = TaskRunStage(id="step-1", agent_name="Agent1")
            repo.update_task_runtime_step("structure-test", step)

            # Verify directory structure
            task_dir = repo._get_task_dir("structure-test")
            assert task_dir.exists()
            assert (task_dir / "task.json").exists()

            steps_dir = repo._get_steps_dir("structure-test")
            assert steps_dir.exists()
            assert (steps_dir / "step_step-1.json").exists()
