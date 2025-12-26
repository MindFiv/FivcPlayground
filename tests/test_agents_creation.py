"""
Tests for agent creation functions in fivcplayground.agents module.

Tests verify:
- create_agent with various agent config IDs
- create_companion_agent, create_tooling_agent, create_consultant_agent
- create_planning_agent, create_research_agent, create_engineering_agent
- create_evaluating_agent
- Error handling for missing configs
- Model resolution
"""

from unittest.mock import Mock, patch
import pytest

from fivcplayground.agents import (
    create_agent,
    AgentBackend,
    # create_companion_agent,
    # create_tooling_agent,
    # create_consultant_agent,
    # create_planning_agent,
    # create_research_agent,
    # create_engineering_agent,
    # create_evaluating_agent,
)
from fivcplayground.agents.types.base import AgentConfig


class TestCreateAgent:
    """Test create_agent function."""

    def test_create_agent_with_valid_config(self):
        """Test creating agent with valid configuration."""
        mock_underlying_model = Mock()
        mock_model_wrapper = Mock()
        mock_model_wrapper.get_underlying.return_value = mock_underlying_model

        mock_agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
            description="Test agent",
            system_prompt="You are helpful",
            tool_ids=["tool1", "tool2"],
        )
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config

        # Create a mock agent backend
        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent = Mock()
        mock_agent.id = "test-agent"
        mock_agent._model = mock_underlying_model
        mock_agent_backend.create_agent.return_value = mock_agent

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model_wrapper

            agent = create_agent(
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_repo,
                agent_config_id="test-agent",
            )

            assert agent.id == "test-agent"
            assert agent._model == mock_underlying_model
            mock_agent_repo.get_agent_config.assert_called_once_with("test-agent")

    def test_create_agent_missing_config(self):
        """Test create_agent raises error when config not found."""
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = None
        mock_agent_backend = Mock(spec=AgentBackend)

        with pytest.raises(ValueError, match="Agent config not found"):
            create_agent(
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_repo,
            )

    def test_create_agent_missing_model(self):
        """Test create_agent raises error when model not found."""
        mock_agent_config = AgentConfig(
            id="test-agent",
            model_id="missing-model",
        )
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config
        mock_agent_backend = Mock(spec=AgentBackend)

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = None

            with pytest.raises(ValueError, match="Model not found"):
                create_agent(
                    agent_backend=mock_agent_backend,
                    agent_config_repository=mock_agent_repo,
                )

    def test_create_agent_default_config_id(self):
        """Test create_agent uses 'default' as default config ID."""
        mock_underlying_model = Mock()
        mock_model_wrapper = Mock()
        mock_model_wrapper.get_underlying.return_value = mock_underlying_model

        mock_agent_config = AgentConfig(id="default", model_id="default")
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config

        mock_agent_backend = Mock(spec=AgentBackend)
        mock_agent = Mock()
        mock_agent_backend.create_agent.return_value = mock_agent

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model_wrapper

            create_agent(
                agent_backend=mock_agent_backend,
                agent_config_repository=mock_agent_repo,
            )

            mock_agent_repo.get_agent_config.assert_called_once_with("default")
