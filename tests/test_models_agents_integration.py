"""
Integration tests for models module with agents module.

Tests verify:
- Agents module correctly imports from models module
- Agent creation functions use the correct model factories
- Model configuration flows through agent creation
- Backward compatibility with agent creation API
- AgentsRunnable is used directly for agent creation
"""

from unittest.mock import patch, MagicMock
from langchain_core.language_models import BaseChatModel

from fivcplayground.agents import (
    create_default_agent,
    create_companion_agent,
    create_tooling_agent,
    create_consultant_agent,
)
from fivcplayground.agents.types import AgentsRunnable


class TestAgentsModuleImports:
    """Test that agents module correctly imports from models module."""

    def test_agents_imports_model_factories(self):
        """Test agents module imports model factory functions."""
        from fivcplayground import agents

        # These should be available through the agents module's imports
        assert hasattr(agents, "create_default_model")
        assert hasattr(agents, "create_chat_model")
        assert hasattr(agents, "create_reasoning_model")

    def test_agents_init_imports_from_models(self):
        """Test agents/__init__.py imports from fivcplayground.models."""
        import fivcplayground.agents as agents_module

        # Check that the module has the imported functions in its namespace
        assert "create_default_model" in dir(agents_module)
        assert "create_chat_model" in dir(agents_module)
        assert "create_reasoning_model" in dir(agents_module)


class TestDefaultAgentModelUsage:
    """Test create_default_agent uses create_default_model and returns AgentsRunnable."""

    @patch("fivcplayground.agents.create_default_model")
    @patch("fivcplayground.agents.tools")
    def test_default_agent_creates_default_model(self, mock_tools, mock_create_model):
        """Test create_default_agent calls create_default_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_model.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_default_agent()

        mock_create_model.assert_called_once()
        assert isinstance(agent, AgentsRunnable)

    @patch("fivcplayground.agents.create_default_model")
    @patch("fivcplayground.agents.tools")
    def test_default_agent_returns_agents_runnable(self, mock_tools, mock_create_model):
        """Test create_default_agent returns AgentsRunnable instance."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_model.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_default_agent()

        assert isinstance(agent, AgentsRunnable)
        assert agent._name == "Generic"

    @patch("fivcplayground.agents.create_default_model")
    @patch("fivcplayground.agents.tools")
    def test_default_agent_respects_provided_model(self, mock_tools, mock_create_model):
        """Test create_default_agent doesn't override provided model."""
        custom_model = MagicMock(spec=BaseChatModel)
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_default_agent(model=custom_model)

        # create_default_model should not be called
        mock_create_model.assert_not_called()

        # Agent should be created with custom model
        assert isinstance(agent, AgentsRunnable)


class TestCompanionAgentModelUsage:
    """Test create_companion_agent uses create_chat_model and returns AgentsRunnable."""

    @patch("fivcplayground.agents.create_chat_model")
    @patch("fivcplayground.agents.tools")
    def test_companion_agent_creates_chat_model(self, mock_tools, mock_create_chat):
        """Test create_companion_agent calls create_chat_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_chat.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_companion_agent()

        mock_create_chat.assert_called_once()
        assert isinstance(agent, AgentsRunnable)

    @patch("fivcplayground.agents.create_chat_model")
    @patch("fivcplayground.agents.tools")
    def test_companion_agent_returns_agents_runnable(
        self, mock_tools, mock_create_chat
    ):
        """Test create_companion_agent returns AgentsRunnable instance."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_chat.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_companion_agent()

        assert isinstance(agent, AgentsRunnable)
        assert agent._name == "Companion"

    @patch("fivcplayground.agents.create_chat_model")
    @patch("fivcplayground.agents.tools")
    def test_companion_agent_respects_provided_model(
        self, mock_tools, mock_create_chat
    ):
        """Test create_companion_agent doesn't override provided model."""
        custom_model = MagicMock(spec=BaseChatModel)
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_companion_agent(model=custom_model)

        # create_chat_model should not be called
        mock_create_chat.assert_not_called()
        assert isinstance(agent, AgentsRunnable)


class TestToolingAgentModelUsage:
    """Test create_tooling_agent uses create_reasoning_model and returns AgentsRunnable."""

    @patch("fivcplayground.agents.create_reasoning_model")
    @patch("fivcplayground.agents.tools")
    def test_tooling_agent_creates_reasoning_model(
        self, mock_tools, mock_create_reasoning
    ):
        """Test create_tooling_agent calls create_reasoning_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_reasoning.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_tooling_agent()

        mock_create_reasoning.assert_called_once()
        assert isinstance(agent, AgentsRunnable)

    @patch("fivcplayground.agents.create_reasoning_model")
    @patch("fivcplayground.agents.tools")
    def test_tooling_agent_returns_agents_runnable(
        self, mock_tools, mock_create_reasoning
    ):
        """Test create_tooling_agent returns AgentsRunnable instance."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_reasoning.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_tooling_agent()

        assert isinstance(agent, AgentsRunnable)
        assert agent._name == "Tooling"


class TestConsultantAgentModelUsage:
    """Test create_consultant_agent uses create_reasoning_model and returns AgentsRunnable."""

    @patch("fivcplayground.agents.create_reasoning_model")
    @patch("fivcplayground.agents.tools")
    def test_consultant_agent_creates_reasoning_model(
        self, mock_tools, mock_create_reasoning
    ):
        """Test create_consultant_agent calls create_reasoning_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_reasoning.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_consultant_agent()

        mock_create_reasoning.assert_called_once()
        assert isinstance(agent, AgentsRunnable)

    @patch("fivcplayground.agents.create_reasoning_model")
    @patch("fivcplayground.agents.tools")
    def test_consultant_agent_returns_agents_runnable(
        self, mock_tools, mock_create_reasoning
    ):
        """Test create_consultant_agent returns AgentsRunnable instance."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_reasoning.return_value = mock_model
        mock_tools.default_retriever.get_all.return_value = []

        agent = create_consultant_agent()

        assert isinstance(agent, AgentsRunnable)
        assert agent._name == "Consultant"


class TestModelMigrationBackwardCompatibility:
    """Test backward compatibility after migration."""

    def test_models_module_is_package(self):
        """Test models is now a package, not a module."""
        import fivcplayground.models as models

        # Should have __path__ attribute (package indicator)
        assert hasattr(models, "__path__")

    def test_direct_imports_work(self):
        """Test direct imports from models work."""
        from fivcplayground.models import (
            create_default_model,
            create_chat_model,
            create_reasoning_model,
            create_coding_model,
        )

        assert callable(create_default_model)
        assert callable(create_chat_model)
        assert callable(create_reasoning_model)
        assert callable(create_coding_model)

    def test_backends_accessible(self):
        """Test backends module is accessible."""
        from fivcplayground.models.backends.langchain import create_model

        assert callable(create_model)

    def test_no_old_models_py_file(self):
        """Test old models.py file doesn't exist."""
        import os

        old_models_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "fivcadvisor", "models.py"
        )

        assert not os.path.exists(old_models_path), "Old models.py file still exists"
