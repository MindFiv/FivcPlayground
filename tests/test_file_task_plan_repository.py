#!/usr/bin/env python3
"""
Tests for FileTaskPlanRepository functionality.
"""

import pytest
import tempfile
import json

from fivcplayground.tasks.types import TaskPlan
from fivcplayground.tasks.types.repositories.files import FileTaskPlanRepository
from fivcplayground.agents import AgentConfig
from fivcplayground.utils import OutputDir


class TestFileTaskPlanRepository:
    """Tests for FileTaskPlanRepository class"""

    def test_initialization(self):
        """Test repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()
            assert repo.plans_dir.exists()
            assert repo.plans_dir.is_dir()

    def test_initialization_creates_plans_directory(self):
        """Test that initialization creates the task_plans subdirectory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            plans_dir = repo.base_path / "task_plans"
            assert plans_dir.exists()
            assert plans_dir.is_dir()

    @pytest.mark.asyncio
    async def test_update_and_get_task_plan(self):
        """Test creating and retrieving a task plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a task plan
            agent = AgentConfig(id="test-agent", backend="test")
            task_plan = TaskPlan(
                id="test-plan-123",
                description="Test task plan",
                agents=[agent],
            )

            # Save task plan
            await repo.update_task_plan_async(task_plan)

            # Verify task plan file exists
            task_plan_file = repo._get_task_plan_file("test-plan-123")
            assert task_plan_file.exists()

            # Retrieve task plan
            retrieved_plan = await repo.get_task_plan_async("test-plan-123")
            assert retrieved_plan is not None
            assert retrieved_plan.id == "test-plan-123"
            assert retrieved_plan.description == "Test task plan"
            assert len(retrieved_plan.agents) == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_plan(self):
        """Test retrieving a task plan that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Try to get non-existent task plan
            task_plan = await repo.get_task_plan_async("nonexistent-plan")
            assert task_plan is None

    @pytest.mark.asyncio
    async def test_delete_task_plan(self):
        """Test deleting a task plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a task plan
            agent = AgentConfig(id="test-agent", backend="test")
            task_plan = TaskPlan(
                id="test-plan-456",
                description="Test task plan",
                agents=[agent],
            )
            await repo.update_task_plan_async(task_plan)

            # Verify task plan exists
            assert await repo.get_task_plan_async("test-plan-456") is not None

            # Delete task plan
            await repo.delete_task_plan_async("test-plan-456")

            # Verify task plan is deleted
            assert await repo.get_task_plan_async("test-plan-456") is None
            assert not repo._get_task_plan_file("test-plan-456").exists()

    @pytest.mark.asyncio
    async def test_list_task_plans(self):
        """Test listing all task plans"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create multiple task plans
            agent = AgentConfig(id="test-agent", backend="test")
            plan1 = TaskPlan(
                id="plan-1",
                description="Plan 1",
                agents=[agent],
            )
            plan2 = TaskPlan(
                id="plan-2",
                description="Plan 2",
                agents=[agent],
            )
            plan3 = TaskPlan(
                id="plan-3",
                description="Plan 3",
                agents=[agent],
            )

            await repo.update_task_plan_async(plan1)
            await repo.update_task_plan_async(plan2)
            await repo.update_task_plan_async(plan3)

            # List task plans
            plans = await repo.list_task_plans_async()
            assert len(plans) == 3

            plan_ids = {plan.id for plan in plans}
            assert "plan-1" in plan_ids
            assert "plan-2" in plan_ids
            assert "plan-3" in plan_ids

    @pytest.mark.asyncio
    async def test_update_existing_task_plan(self):
        """Test updating an existing task plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a task plan
            agent = AgentConfig(id="test-agent", backend="test")
            task_plan = TaskPlan(
                id="test-plan-update",
                description="Original description",
                agents=[agent],
            )
            await repo.update_task_plan_async(task_plan)

            # Update task plan
            task_plan.description = "Updated description"
            await repo.update_task_plan_async(task_plan)

            # Retrieve and verify
            retrieved_plan = await repo.get_task_plan_async("test-plan-update")
            assert retrieved_plan.description == "Updated description"

    @pytest.mark.asyncio
    async def test_storage_structure(self):
        """Test that the storage structure matches the expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a task plan
            agent = AgentConfig(id="test-agent", backend="test")
            task_plan = TaskPlan(
                id="structure-test",
                description="Test",
                agents=[agent],
            )
            await repo.update_task_plan_async(task_plan)

            # Verify directory structure
            plans_dir = repo.base_path / "task_plans"
            assert plans_dir.exists()
            assert (plans_dir / "structure-test.json").exists()

    @pytest.mark.asyncio
    async def test_json_file_format(self):
        """Test that task plans are stored as valid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a task plan
            agent = AgentConfig(id="test-agent", backend="test")
            task_plan = TaskPlan(
                id="json-test",
                description="Test JSON format",
                agents=[agent],
            )
            await repo.update_task_plan_async(task_plan)

            # Read and verify JSON file
            task_plan_file = repo._get_task_plan_file("json-test")
            with open(task_plan_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["id"] == "json-test"
            assert data["description"] == "Test JSON format"
            assert len(data["agents"]) == 1

    @pytest.mark.asyncio
    async def test_corrupted_json_file_handling(self):
        """Test handling of corrupted JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # Create a corrupted JSON file
            task_plan_file = repo._get_task_plan_file("corrupted")
            task_plan_file.parent.mkdir(parents=True, exist_ok=True)
            with open(task_plan_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json }")

            # Try to get corrupted task plan
            task_plan = await repo.get_task_plan_async("corrupted")
            assert task_plan is None

    @pytest.mark.asyncio
    async def test_empty_list_when_no_plans(self):
        """Test that list returns empty list when no plans exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskPlanRepository(output_dir=output_dir)

            # List task plans when none exist
            plans = await repo.list_task_plans_async()
            assert plans == []
