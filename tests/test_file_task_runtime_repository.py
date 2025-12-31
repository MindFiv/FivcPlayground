#!/usr/bin/env python3
"""
Tests for FileTaskRunRepository functionality.
"""

import pytest
import tempfile
from datetime import datetime

from fivcplayground.tasks.types import TaskRun, TaskRunStatus
from fivcplayground.tasks.types.repositories.files import FileTaskRunRepository
from fivcplayground.utils import OutputDir


class TestFileTaskRunRepository:
    """Tests for FileTaskRunRepository class"""

    def test_initialization(self):
        """Test repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    @pytest.mark.asyncio
    async def test_update_and_get_task(self):
        """Test creating and retrieving a task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(
                id="test-task-123",
                status=TaskRunStatus.EXECUTING,
                started_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            # Save task
            await repo.update_task_run_async(task)

            # Verify task file exists
            task_file = repo._get_task_file("test-task-123")
            assert task_file.exists()

            # Retrieve task
            retrieved_task = await repo.get_task_run_async("test-task-123")
            assert retrieved_task is not None
            assert retrieved_task.id == "test-task-123"
            assert retrieved_task.status == TaskRunStatus.EXECUTING
            assert retrieved_task.started_at == datetime(2024, 1, 1, 12, 0, 0)

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self):
        """Test retrieving a task that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Try to get non-existent task
            task = await repo.get_task_run_async("nonexistent-task")
            assert task is None

    @pytest.mark.asyncio
    async def test_delete_task(self):
        """Test deleting a task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(id="test-task-456")
            await repo.update_task_run_async(task)

            # Verify task exists
            assert await repo.get_task_run_async("test-task-456") is not None

            # Delete task
            await repo.delete_task_run_async("test-task-456")

            # Verify task is deleted
            assert await repo.get_task_run_async("test-task-456") is None
            assert not repo._get_task_dir("test-task-456").exists()

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """Test listing all tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Create multiple tasks
            task1 = TaskRun(id="task-1", status=TaskRunStatus.PENDING)
            task2 = TaskRun(id="task-2", status=TaskRunStatus.EXECUTING)
            task3 = TaskRun(id="task-3", status=TaskRunStatus.COMPLETED)

            await repo.update_task_run_async(task1)
            await repo.update_task_run_async(task2)
            await repo.update_task_run_async(task3)

            # List tasks
            tasks = await repo.list_task_runs_async()
            assert len(tasks) == 3

            task_ids = {task.id for task in tasks}
            assert "task-1" in task_ids
            assert "task-2" in task_ids
            assert "task-3" in task_ids

    @pytest.mark.asyncio
    async def test_update_existing_task(self):
        """Test updating an existing task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(
                id="test-task-update",
                status=TaskRunStatus.PENDING,
            )
            await repo.update_task_run_async(task)

            # Update task status
            task.status = TaskRunStatus.COMPLETED
            task.completed_at = datetime(2024, 1, 1, 13, 0, 0)
            await repo.update_task_run_async(task)

            # Retrieve and verify
            retrieved_task = await repo.get_task_run_async("test-task-update")
            assert retrieved_task.status == TaskRunStatus.COMPLETED
            assert retrieved_task.completed_at == datetime(2024, 1, 1, 13, 0, 0)

    @pytest.mark.asyncio
    async def test_storage_structure(self):
        """Test that the storage structure matches the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRunRepository(output_dir=output_dir)

            # Create a task
            task = TaskRun(id="structure-test")
            await repo.update_task_run_async(task)

            # Verify directory structure
            task_dir = repo._get_task_dir("structure-test")
            assert task_dir.exists()
            assert (task_dir / "task.json").exists()
