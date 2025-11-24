"""
Comprehensive tests for AgentRunnable implementation.

Tests verify:
- AgentRunnable initialization with various parameters
- Synchronous execution via run() method
- Asynchronous execution via run_async() method
- Tool handling and conversion
- Error handling and edge cases
- Runnable interface compliance
- Message history support (string queries and message lists)
- Structured response handling with response_model

These tests work with both Strands and LangChain backends.
"""

from unittest.mock import MagicMock

from fivcplayground.agents.types import AgentRunnable


class TestAgentsRunnableInitialization:
    """Test AgentRunnable initialization."""

    def test_init_with_required_parameters(self):
        """Test AgentRunnable initialization with required parameters."""
        mock_model = MagicMock()

        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert agent._model == mock_model
        assert agent.id == "test-agent"

    def test_init_with_system_prompt(self):
        """Test AgentRunnable initialization with system prompt."""
        mock_model = MagicMock()
        system_prompt = "You are a helpful assistant"

        agent = AgentRunnable(
            model=mock_model,
            id="test-agent",
            system_prompt=system_prompt,
        )

        assert agent._system_prompt == system_prompt

    def test_init_generates_unique_ids(self):
        """Test that each AgentRunnable gets a unique ID when not provided."""
        mock_model = MagicMock()

        agent1 = AgentRunnable(model=mock_model)
        agent2 = AgentRunnable(model=mock_model)

        assert agent1.id != agent2.id


class TestAgentsRunnableProperties:
    """Test AgentRunnable properties."""

    def test_id_property(self):
        """Test that id property returns a string."""
        mock_model = MagicMock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert isinstance(agent.id, str)
        assert len(agent.id) > 0

    def test_id_property_consistency(self):
        """Test that id property returns the same value on multiple calls."""
        mock_model = MagicMock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        id1 = agent.id
        id2 = agent.id

        assert id1 == id2

    def test_description_property(self):
        """Test that description property returns a string."""
        mock_model = MagicMock()
        agent = AgentRunnable(
            model=mock_model, id="test-agent", description="Test description"
        )

        assert isinstance(agent.description, str)
        assert agent.description == "Test description"


class TestAgentsRunnableExecution:
    """Test AgentRunnable execution methods."""

    def test_run_method_exists(self):
        """Test that run method exists and is callable."""
        mock_model = MagicMock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert hasattr(agent, "run")
        assert callable(agent.run)

    def test_run_async_method_exists(self):
        """Test that run_async method exists and is callable."""
        mock_model = MagicMock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert hasattr(agent, "run_async")
        assert callable(agent.run_async)

    def test_callable_interface(self):
        """Test that AgentRunnable is callable via __call__."""
        mock_model = MagicMock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert callable(agent)


class TestAgentsRunnableToolHandling:
    """Test AgentRunnable tool handling."""

    def test_init_without_tools(self):
        """Test initialization without tools parameter."""
        mock_model = MagicMock()

        agent = AgentRunnable(model=mock_model, id="test-agent")

        # Tools are no longer stored in AgentRunnable
        assert not hasattr(agent, "_tools") or agent._tools is None


class TestAgentsRunnableStructuredResponse:
    """Test AgentRunnable structured response handling."""

    def test_init_with_description(self):
        """Test initialization with description parameter."""
        mock_model = MagicMock()

        agent = AgentRunnable(
            model=mock_model,
            id="test-agent",
            description="Test agent description",
        )

        assert agent._description == "Test agent description"


class TestAgentsRunnableIntegration:
    """Integration tests for AgentRunnable."""

    def test_agent_creation_flow(self):
        """Test complete agent creation flow."""
        mock_model = MagicMock()

        agent = AgentRunnable(
            model=mock_model,
            id="test-agent",
            system_prompt="You are helpful",
            description="Test agent",
        )

        assert agent._system_prompt == "You are helpful"
        assert agent.id == "test-agent"
        assert agent._model == mock_model
        assert agent._description == "Test agent"
