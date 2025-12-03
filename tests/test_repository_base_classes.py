"""
Tests for repository base classes and interfaces.

Tests verify:
- Abstract base class enforcement
- Repository interface contracts
- Error handling in repository operations
"""

import pytest

from fivcplayground.agents.types.repositories.base import (
    AgentConfigRepository,
    AgentRunRepository,
)
from fivcplayground.models.types.repositories.base import ModelConfigRepository
from fivcplayground.embeddings.types.repositories.base import (
    EmbeddingConfigRepository,
)
from fivcplayground.tools.types.repositories.base import ToolConfigRepository


class TestAgentConfigRepositoryInterface:
    """Test AgentConfigRepository interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            AgentConfigRepository()

    def test_requires_update_agent_config(self):
        """Test that subclass must implement update_agent_config."""

        class IncompleteRepo(AgentConfigRepository):
            def get_agent_config(self, agent_id):
                pass

            def list_agent_configs(self):
                pass

            def delete_agent_config(self, agent_id):
                pass

        with pytest.raises(TypeError):
            IncompleteRepo()

    def test_requires_get_agent_config(self):
        """Test that subclass must implement get_agent_config."""

        class IncompleteRepo(AgentConfigRepository):
            def update_agent_config(self, agent_config):
                pass

            def list_agent_configs(self):
                pass

            def delete_agent_config(self, agent_id):
                pass

        with pytest.raises(TypeError):
            IncompleteRepo()

    def test_requires_list_agent_configs(self):
        """Test that subclass must implement list_agent_configs."""

        class IncompleteRepo(AgentConfigRepository):
            def update_agent_config(self, agent_config):
                pass

            def get_agent_config(self, agent_id):
                pass

            def delete_agent_config(self, agent_id):
                pass

        with pytest.raises(TypeError):
            IncompleteRepo()

    def test_requires_delete_agent_config(self):
        """Test that subclass must implement delete_agent_config."""

        class IncompleteRepo(AgentConfigRepository):
            def update_agent_config(self, agent_config):
                pass

            def get_agent_config(self, agent_id):
                pass

            def list_agent_configs(self):
                pass

        with pytest.raises(TypeError):
            IncompleteRepo()


class TestModelConfigRepositoryInterface:
    """Test ModelConfigRepository interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            ModelConfigRepository()


class TestEmbeddingConfigRepositoryInterface:
    """Test EmbeddingConfigRepository interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            EmbeddingConfigRepository()


class TestToolConfigRepositoryInterface:
    """Test ToolConfigRepository interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            ToolConfigRepository()


class TestAgentRunRepositoryInterface:
    """Test AgentRunRepository interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            AgentRunRepository()
