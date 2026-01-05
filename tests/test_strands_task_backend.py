#!/usr/bin/env python3
"""
Tests for StrandsTaskBackend.

Tests the Strands implementation of the TaskBackend interface.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pydantic import BaseModel

from fivcplayground.backends.strands.tasks import StrandsTaskBackend
from fivcplayground.tasks.types import TaskPlan, TaskPlanAgent
from fivcplayground.agents import AgentBackend, AgentConfigRepository, AgentRunnable
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
    async def test_create_task_async_no_agents(self):
        """Test create_task_async raises error when no agents specified."""
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

        with pytest.raises(RuntimeError, match="No agents specified for task"):
            await backend.create_task_async(
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                task_plan=task_plan,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_single_agent(self):
        """Test create_task_async with single agent."""
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

        # Mock the agent runnable
        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "test-agent"
        mock_agent_runnable.name = "test-agent"
        mock_agent_runnable.description = "Test agent"

        mock_agent_backend = AsyncMock(spec=AgentBackend)
        mock_agent_backend.create_agent_async = AsyncMock(
            return_value=mock_agent_runnable
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        result = await backend.create_task_async(
            model_backend=mock_model_backend,
            model_config_repository=mock_model_config_repo,
            agent_backend=mock_agent_backend,
            agent_config_repository=mock_agent_config_repo,
            task_plan=task_plan,
            task_query_template="Test: {query}",
            task_response_model=MockResponse,
        )

        assert result is not None
        assert result.id == "test-agent"
        mock_agent_backend.create_agent_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_async_multiple_agents(self):
        """Test create_task_async raises NotImplementedError for multiple agents."""
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
            await backend.create_task_async(
                model_backend=mock_model_backend,
                model_config_repository=mock_model_config_repo,
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_config_repo,
                task_plan=task_plan,
            )

    @pytest.mark.asyncio
    async def test_create_task_async_with_response_model(self):
        """Test create_task_async passes response_model to SimpleTaskRunnable."""
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

        mock_agent_runnable = Mock(spec=AgentRunnable)
        mock_agent_runnable.id = "test-agent"

        mock_agent_backend = AsyncMock(spec=AgentBackend)
        mock_agent_backend.create_agent_async = AsyncMock(
            return_value=mock_agent_runnable
        )

        mock_model_backend = Mock(spec=ModelBackend)
        mock_model_config_repo = Mock(spec=ModelConfigRepository)
        mock_agent_config_repo = Mock(spec=AgentConfigRepository)

        result = await backend.create_task_async(
            model_backend=mock_model_backend,
            model_config_repository=mock_model_config_repo,
            agent_backend=mock_agent_backend,
            agent_config_repository=mock_agent_config_repo,
            task_plan=task_plan,
            task_response_model=MockResponse,
            task_query_template="Query: {query}",
        )

        assert result is not None
        # Verify the response model was passed through kwargs
        assert hasattr(result, "_kwargs")
        assert result._kwargs.get("response_model") == MockResponse
