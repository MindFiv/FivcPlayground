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
    create_planned_task_async,
    create_tooling_task_async,
    create_briefing_task_async,
    create_assessing_task_async,
    create_planning_task_async,
)
from fivcplayground.tasks.types import TaskPlan
from fivcplayground.agents import AgentBackend, AgentRunnable, AgentConfigRepository


class TestTaskCreationFunctions:
    """Tests for task creation helper functions."""

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_no_backend(self):
        """Test create_tooling_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No agent backend specified"):
            await create_tooling_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_no_backend_no_exception(self):
        """Test create_tooling_task_async with no backend returns None."""
        result = await create_tooling_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_no_backend(self):
        """Test create_briefing_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No agent backend specified"):
            await create_briefing_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_no_backend_no_exception(self):
        """Test create_briefing_task_async with no backend returns None."""
        result = await create_briefing_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_no_backend(self):
        """Test create_assessing_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No agent backend specified"):
            await create_assessing_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_no_backend_no_exception(self):
        """Test create_assessing_task_async with no backend returns None."""
        result = await create_assessing_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_planning_task_async_no_backend(self):
        """Test create_planning_task_async with no backend raises error."""
        with pytest.raises(RuntimeError, match="No agent backend specified"):
            await create_planning_task_async(raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_planning_task_async_no_backend_no_exception(self):
        """Test create_planning_task_async with no backend returns None."""
        result = await create_planning_task_async(raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_tooling_task_async_with_mock_backend(self):
        """Test create_tooling_task_async with mock backend."""
        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "tooling"
        mock_agent_runnable.name = "tooling"
        mock_agent_runnable.description = "Tooling task"

        mock_backend = AsyncMock(spec=AgentBackend)
        mock_backend.create_agent_async = AsyncMock(return_value=mock_agent_runnable)

        result = await create_tooling_task_async(
            agent_backend=mock_backend,
            raise_exception=True,
        )

        assert result is not None
        # BoundedAgentRunnable wraps the agent, so check it's not None
        assert result is not None
        mock_backend.create_agent_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_briefing_task_async_with_mock_backend(self):
        """Test create_briefing_task_async with mock backend."""
        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "briefing"

        mock_backend = AsyncMock(spec=AgentBackend)
        mock_backend.create_agent_async = AsyncMock(return_value=mock_agent_runnable)

        result = await create_briefing_task_async(
            agent_backend=mock_backend,
        )

        assert result is not None
        # BoundedAgentRunnable wraps the agent, so check it's not None
        mock_backend.create_agent_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_assessing_task_async_with_mock_backend(self):
        """Test create_assessing_task_async with mock backend."""
        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "assessment"

        mock_backend = AsyncMock(spec=AgentBackend)
        mock_backend.create_agent_async = AsyncMock(return_value=mock_agent_runnable)

        result = await create_assessing_task_async(
            agent_backend=mock_backend,
        )

        assert result is not None
        # BoundedAgentRunnable wraps the agent, so check it's not None
        mock_backend.create_agent_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_planning_task_async_with_mock_backend(self):
        """Test create_planning_task_async with mock backend."""
        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "planning"

        mock_backend = AsyncMock(spec=AgentBackend)
        mock_backend.create_agent_async = AsyncMock(return_value=mock_agent_runnable)

        result = await create_planning_task_async(
            agent_backend=mock_backend,
        )

        assert result is not None
        # BoundedAgentRunnable wraps the agent, so check it's not None
        mock_backend.create_agent_async.assert_called_once()


class TestCreateTaskAsync:
    """Tests for create_planned_task_async function."""

    @pytest.mark.asyncio
    async def test_create_task_async_no_plan(self):
        """Test create_planned_task_async with no plan raises error."""
        with pytest.raises(ValueError, match="Task plan is required"):
            await create_planned_task_async(task_plan=None, raise_exception=True)

    @pytest.mark.asyncio
    async def test_create_task_async_no_plan_no_exception(self):
        """Test create_planned_task_async with no plan returns None."""
        result = await create_planned_task_async(task_plan=None, raise_exception=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_with_plan_not_implemented(self):
        """Test create_planned_task_async with plan raises NotImplementedError."""
        task_plan = TaskPlan(
            id="test-plan",
            description="Test plan",
            agents=[],
        )
        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented yet"
        ):
            await create_planned_task_async(
                task_plan=task_plan,
                raise_exception=True,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_with_plan_not_implemented_no_exception(self):
        """Test create_planned_task_async with plan returns None on error."""
        task_plan = TaskPlan(
            id="test-plan",
            description="Test plan",
            agents=[],
        )
        result = await create_planned_task_async(
            task_plan=task_plan,
            raise_exception=False,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_with_all_parameters(self):
        """Test create_planned_task_async with all optional parameters."""
        task_plan = TaskPlan(
            id="test-plan",
            description="Test plan",
            agents=[],
        )
        mock_agent_backend = AsyncMock(spec=AgentBackend)
        mock_agent_config_repo = AsyncMock(spec=AgentConfigRepository)

        # Should raise NotImplementedError since implementation is not complete
        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented yet"
        ):
            await create_planned_task_async(
                task_plan=task_plan,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                raise_exception=True,
            )
