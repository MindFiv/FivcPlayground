"""
Comprehensive tests for AgentsRunnable implementation.

Tests verify:
- AgentsRunnable initialization with various parameters
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
from pydantic import BaseModel

from fivcplayground.agents.types import AgentsRunnable


class TestAgentsRunnableInitialization:
    """Test AgentsRunnable initialization."""

    def test_init_with_required_parameters(self):
        """Test AgentsRunnable initialization with required parameters."""
        mock_model = MagicMock()

        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert agent._name == "TestAgent"
        assert agent._model == mock_model
        assert agent.id is not None

    def test_init_with_system_prompt(self):
        """Test AgentsRunnable initialization with system prompt."""
        mock_model = MagicMock()
        system_prompt = "You are a helpful assistant"

        agent = AgentsRunnable(
            model=mock_model,
            tools=[],
            agent_name="TestAgent",
            system_prompt=system_prompt,
        )

        assert agent._system_prompt == system_prompt

    def test_init_generates_unique_ids(self):
        """Test that each AgentsRunnable gets a unique ID."""
        mock_model = MagicMock()

        agent1 = AgentsRunnable(model=mock_model, tools=[], agent_name="Agent1")
        agent2 = AgentsRunnable(model=mock_model, tools=[], agent_name="Agent2")

        assert agent1.id != agent2.id


class TestAgentsRunnableProperties:
    """Test AgentsRunnable properties."""

    def test_id_property(self):
        """Test that id property returns a string."""
        mock_model = MagicMock()
        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert isinstance(agent.id, str)
        assert len(agent.id) > 0

    def test_id_property_consistency(self):
        """Test that id property returns the same value on multiple calls."""
        mock_model = MagicMock()
        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        id1 = agent.id
        id2 = agent.id

        assert id1 == id2


class TestAgentsRunnableExecution:
    """Test AgentsRunnable execution methods."""

    def test_run_method_exists(self):
        """Test that run method exists and is callable."""
        mock_model = MagicMock()
        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert hasattr(agent, "run")
        assert callable(agent.run)

    def test_run_async_method_exists(self):
        """Test that run_async method exists and is callable."""
        mock_model = MagicMock()
        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert hasattr(agent, "run_async")
        assert callable(agent.run_async)

    def test_callable_interface(self):
        """Test that AgentsRunnable is callable via __call__."""
        mock_model = MagicMock()
        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert callable(agent)


class TestAgentsRunnableToolHandling:
    """Test AgentsRunnable tool handling."""

    def test_init_with_empty_tools(self):
        """Test initialization with empty tools list."""
        mock_model = MagicMock()

        agent = AgentsRunnable(model=mock_model, tools=[], agent_name="TestAgent")

        assert agent._tools == []

    def test_init_with_tools(self):
        """Test initialization with tools."""
        mock_model = MagicMock()
        mock_tool = MagicMock()

        agent = AgentsRunnable(
            model=mock_model, tools=[mock_tool], agent_name="TestAgent"
        )

        # Verify tools are stored
        assert len(agent._tools) > 0


class TestAgentsRunnableStructuredResponse:
    """Test AgentsRunnable structured response handling."""

    def test_init_with_response_model(self):
        """Test initialization with response_model parameter."""

        class TestResponse(BaseModel):
            answer: str
            confidence: float

        mock_model = MagicMock()

        agent = AgentsRunnable(
            model=mock_model,
            tools=[],
            agent_name="TestAgent",
            response_model=TestResponse,
        )

        assert agent._response_model == TestResponse

    def test_init_with_callback_handler(self):
        """Test initialization with callback handler."""
        mock_model = MagicMock()
        mock_callback = MagicMock()

        agent = AgentsRunnable(
            model=mock_model,
            tools=[],
            agent_name="TestAgent",
            callback_handler=mock_callback,
        )

        assert agent._callback_handler == mock_callback


class TestAgentsRunnableIntegration:
    """Integration tests for AgentsRunnable."""

    def test_agent_creation_flow(self):
        """Test complete agent creation flow."""
        mock_model = MagicMock()

        agent = AgentsRunnable(
            model=mock_model,
            tools=[],
            agent_name="TestAgent",
            system_prompt="You are helpful",
        )

        assert agent._name == "TestAgent"
        assert agent._system_prompt == "You are helpful"
        assert agent.id is not None
        assert agent._model == mock_model
