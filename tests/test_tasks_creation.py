#!/usr/bin/env python3
"""
Tests for task creation functions.

Tests the public API functions for creating specialized tasks:
- create_tooling_task_async
- create_briefing_task_async
- create_assessing_task_async
- create_planning_task_async
"""

import pytest
from unittest.mock import AsyncMock, Mock

from fivcplayground.tasks import (
    create_task_async,
    create_tooling_task_async,
    create_briefing_task_async,
    create_assessing_task_async,
    create_planning_task_async,
)
from fivcplayground.tasks.types import TaskPlan, TaskPlanRepository
from fivcplayground.backends.strands import StrandsTaskBackend
from fivcplayground.agents import AgentBackend
# from fivcplayground.models import ModelBackend, ModelConfigRepository


class TestTaskCreationFunctions:
    """Tests for task creation helper functions."""

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_no_backend(self):
        """Test create_tooling_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No task backend specified"):
            await create_tooling_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_no_backend_no_exception(self):
        """Test create_tooling_task_async with no backend returns None."""
        result = await create_tooling_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_no_backend(self):
        """Test create_briefing_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No task backend specified"):
            await create_briefing_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_no_backend_no_exception(self):
        """Test create_briefing_task_async with no backend returns None."""
        result = await create_briefing_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_no_backend(self):
        """Test create_assessing_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No task backend specified"):
            await create_assessing_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_no_backend_no_exception(self):
        """Test create_assessing_task_async with no backend returns None."""
        result = await create_assessing_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_planning_task_async_no_backend(self):
        """Test create_planning_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No task backend specified"):
            await create_planning_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_planning_task_async_no_backend_no_exception(self):
        """Test create_planning_task_async with no backend returns None."""
        result = await create_planning_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_with_mock_backend(self):
        """Test create_tooling_task_async with mock backend."""
        mock_backend = AsyncMock(spec=AgentBackend)
        mock_runnable = Mock()
        mock_runnable.id = "tooling"
        mock_runnable.name = "tooling"
        mock_runnable.description = "Tooling task"

        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_task_backend.create_task_async = AsyncMock(return_value=mock_runnable)

        result = await create_tooling_task_async(
            task_backend=mock_task_backend,
            agent_backend=mock_backend,
            raise_exception=True,
        )

        assert result is not None
        assert result.id == "tooling"
        mock_task_backend.create_task_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_with_mock_backend(self):
        """Test create_briefing_task_async with mock backend."""
        mock_backend = AsyncMock(spec=AgentBackend)
        mock_runnable = Mock()
        mock_runnable.id = "briefing"

        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_task_backend.create_task_async = AsyncMock(return_value=mock_runnable)

        result = await create_briefing_task_async(
            task_backend=mock_task_backend,
            agent_backend=mock_backend,
        )

        assert result is not None
        assert result.id == "briefing"

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_with_mock_backend(self):
        """Test create_assessing_task_async with mock backend."""
        mock_backend = AsyncMock(spec=AgentBackend)
        mock_runnable = Mock()
        mock_runnable.id = "assessment"

        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_task_backend.create_task_async = AsyncMock(return_value=mock_runnable)

        result = await create_assessing_task_async(
            task_backend=mock_task_backend,
            agent_backend=mock_backend,
        )

        assert result is not None
        assert result.id == "assessment"

    @pytest.mark.asyncio
    async def test_create_planning_task_async_with_mock_backend(self):
        """Test create_planning_task_async with mock backend."""
        mock_backend = AsyncMock(spec=AgentBackend)
        mock_runnable = Mock()
        mock_runnable.id = "planning"

        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_task_backend.create_task_async = AsyncMock(return_value=mock_runnable)

        result = await create_planning_task_async(
            task_backend=mock_task_backend,
            agent_backend=mock_backend,
        )

        assert result is not None
        assert result.id == "planning"


class TestCreateTaskAsync:
    """Tests for create_task_async function."""

    @pytest.mark.asyncio
    async def test_create_task_async_no_backend(self):
        """Test create_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No task backend specified"):
            await create_task_async(task_backend=None, raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_task_async_no_backend_no_exception(self):
        """Test create_task_async with no backend returns None."""
        result = await create_task_async(task_backend=None, raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_no_repository(self):
        """Test create_task_async with no repository raises error."""
        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        with pytest.raises(RuntimeError, match="No task plan repository specified"):
            await create_task_async(
                task_backend=mock_task_backend,
                task_plan_repository=None,
                raise_exception=True,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_no_repository_no_exception(self):
        """Test create_task_async with no repository returns None."""
        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        result = await create_task_async(
            task_backend=mock_task_backend,
            task_plan_repository=None,
            raise_exception=False,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_plan_not_found(self):
        """Test create_task_async when plan not found raises error."""
        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_repository = AsyncMock(spec=TaskPlanRepository)
        mock_repository.get_task_plan_async = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Task plan not found"):
            await create_task_async(
                task_backend=mock_task_backend,
                task_plan_repository=mock_repository,
                task_plan_id="nonexistent",
                raise_exception=True,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_plan_not_found_no_exception(self):
        """Test create_task_async when plan not found returns None."""
        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_repository = AsyncMock(spec=TaskPlanRepository)
        mock_repository.get_task_plan_async = AsyncMock(return_value=None)

        result = await create_task_async(
            task_backend=mock_task_backend,
            task_plan_repository=mock_repository,
            task_plan_id="nonexistent",
            raise_exception=False,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_success(self):
        """Test create_task_async successfully creates task."""
        mock_task_backend = AsyncMock(spec=StrandsTaskBackend)
        mock_runnable = Mock()
        mock_runnable.id = "test-task"
        mock_task_backend.create_task_async = AsyncMock(return_value=mock_runnable)

        task_plan = TaskPlan(
            id="test-plan",
            description="Test plan",
            agents=[],
        )
        mock_repository = AsyncMock(spec=TaskPlanRepository)
        mock_repository.get_task_plan_async = AsyncMock(return_value=task_plan)

        result = await create_task_async(
            task_backend=mock_task_backend,
            task_plan_repository=mock_repository,
            task_plan_id="test-plan",
        )

        assert result is not None
        assert result.id == "test-task"
        mock_task_backend.create_task_async.assert_called_once()
