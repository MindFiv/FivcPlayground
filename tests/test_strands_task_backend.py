#!/usr/bin/env python3
"""
Tests for StrandsTaskBackend.

Tests the Strands implementation of the TaskBackend interface.
"""

import pytest
from unittest.mock import Mock
from pydantic import BaseModel

from fivcplayground.backends.strands.tasks import StrandsTaskBackend
from fivcplayground.tasks.types import TaskPlan, TaskPlanAgent
from fivcplayground.agents import AgentBackend, AgentConfigRepository
from fivcplayground.models import ModelBackend, ModelConfigRepository


class MockResponse(BaseModel):
    """Mock response model for testing."""

    result: str


class TestStrandsTaskBackend:
    """Tests for StrandsTaskBackend class."""

    def test_init(self):
        """Test StrandsTaskBackend initialization."""
        backend = StrandsTaskBackend()
        assert backend is not None

    @pytest.mark.asyncio
    async def test_create_task_async_no_plan(self):
        """Test create_planned_task_async with no plan raises ValueError."""
        backend = StrandsTaskBackend()

        with pytest.raises(ValueError, match="Task plan is required"):
            await backend.create_planned_task_async(
                task_plan=None,
                raise_exception=True,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_no_plan_no_exception(self):
        """Test create_planned_task_async with no plan returns None."""
        backend = StrandsTaskBackend()

        result = await backend.create_planned_task_async(
            task_plan=None,
            raise_exception=False,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_task_async_no_agents(self):
        """Test create_planned_task_async raises NotImplementedError."""
        backend = StrandsTaskBackend()

        task_plan = TaskPlan(
            id="test",
            description="Test task",
            agents=[],  # No agents
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented"
        ):
            await backend.create_planned_task_async(
                task_plan=task_plan,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_single_agent(self):
        """Test create_planned_task_async raises NotImplementedError for single agent."""
        backend = StrandsTaskBackend()

        agent_config = TaskPlanAgent(
            id="test-agent",
            model_id="default",
            description="Test agent",
            tool_ids=[],
            system_prompt="Test prompt",
        )

        task_plan = TaskPlan(
            id="test",
            description="Test task",
            agents=[agent_config],
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented"
        ):
            await backend.create_planned_task_async(
                task_plan=task_plan,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_multiple_agents(self):
        """Test create_planned_task_async raises NotImplementedError for multiple agents."""
        backend = StrandsTaskBackend()

        agent_config1 = TaskPlanAgent(
            id="agent1",
            model_id="default",
            description="Agent 1",
        )
        agent_config2 = TaskPlanAgent(
            id="agent2",
            model_id="default",
            description="Agent 2",
        )

        task_plan = TaskPlan(
            id="test",
            description="Test task",
            agents=[agent_config1, agent_config2],
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented"
        ):
            await backend.create_planned_task_async(
                task_plan=task_plan,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_with_response_model(self):
        """Test create_planned_task_async raises NotImplementedError with response_model."""
        backend = StrandsTaskBackend()

        agent_config = TaskPlanAgent(
            id="test-agent",
            model_id="default",
            description="Test agent",
        )

        task_plan = TaskPlan(
            id="test",
            description="Test task",
            agents=[agent_config],
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        with pytest.raises(
            NotImplementedError, match="Multi-agent tasks not implemented"
        ):
            await backend.create_planned_task_async(
                task_plan=task_plan,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
            )
