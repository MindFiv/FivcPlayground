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
    create_companion_agent,
    create_tooling_agent,
    create_consultant_agent,
    create_planning_agent,
    create_research_agent,
    create_engineering_agent,
    create_evaluating_agent,
)
from fivcplayground.agents.types.base import AgentConfig


class TestCreateAgent:
    """Test create_agent function."""

    def test_create_agent_with_valid_config(self):
        """Test creating agent with valid configuration."""
        mock_model = Mock()
        mock_agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
            description="Test agent",
            system_prompt="You are helpful",
        )
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_agent(
                agent_config_repository=mock_agent_repo,
                agent_config_id="test-agent",
            )

            assert agent.id == "test-agent"
            assert agent._model == mock_model
            mock_agent_repo.get_agent_config.assert_called_once_with("test-agent")

    def test_create_agent_missing_config(self):
        """Test create_agent raises error when config not found."""
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = None

        with pytest.raises(ValueError, match="Agent config not found"):
            create_agent(agent_config_repository=mock_agent_repo)

    def test_create_agent_missing_model(self):
        """Test create_agent raises error when model not found."""
        mock_agent_config = AgentConfig(
            id="test-agent",
            model_id="missing-model",
        )
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = None

            with pytest.raises(ValueError, match="Model not found"):
                create_agent(agent_config_repository=mock_agent_repo)

    def test_create_agent_default_config_id(self):
        """Test create_agent uses 'default' as default config ID."""
        mock_model = Mock()
        mock_agent_config = AgentConfig(id="default", model_id="default")
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            create_agent(agent_config_repository=mock_agent_repo)

            mock_agent_repo.get_agent_config.assert_called_once_with("default")


class TestSpecializedAgentCreation:
    """Test specialized agent creation functions."""

    def _setup_mocks(self, agent_id):
        """Helper to setup mocks for agent creation."""
        mock_model = Mock()
        mock_agent_config = AgentConfig(
            id=agent_id,
            model_id="test-model",
            description=f"{agent_id} agent",
        )
        mock_agent_repo = Mock()
        mock_agent_repo.get_agent_config.return_value = mock_agent_config
        return mock_model, mock_agent_repo

    def test_create_companion_agent(self):
        """Test create_companion_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("companion")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_companion_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "companion"
            mock_agent_repo.get_agent_config.assert_called_once_with("companion")

    def test_create_tooling_agent(self):
        """Test create_tooling_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("tooling")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_tooling_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "tooling"
            mock_agent_repo.get_agent_config.assert_called_once_with("tooling")

    def test_create_consultant_agent(self):
        """Test create_consultant_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("consultant")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_consultant_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "consultant"
            mock_agent_repo.get_agent_config.assert_called_once_with("consultant")

    def test_create_planning_agent(self):
        """Test create_planning_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("planner")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_planning_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "planner"
            mock_agent_repo.get_agent_config.assert_called_once_with("planner")

    def test_create_research_agent(self):
        """Test create_research_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("researcher")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_research_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "researcher"
            mock_agent_repo.get_agent_config.assert_called_once_with("researcher")

    def test_create_engineering_agent(self):
        """Test create_engineering_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("engineer")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_engineering_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "engineer"
            mock_agent_repo.get_agent_config.assert_called_once_with("engineer")

    def test_create_evaluating_agent(self):
        """Test create_evaluating_agent."""
        mock_model, mock_agent_repo = self._setup_mocks("evaluator")

        with patch("fivcplayground.agents.create_model") as mock_create_model:
            mock_create_model.return_value = mock_model

            agent = create_evaluating_agent(agent_config_repository=mock_agent_repo)

            assert agent.id == "evaluator"
            mock_agent_repo.get_agent_config.assert_called_once_with("evaluator")
