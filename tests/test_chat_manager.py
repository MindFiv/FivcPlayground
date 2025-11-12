#!/usr/bin/env python3
"""
Tests for Chat functionality.

Tests the chat utility for handling conversation state and agent execution:
- Initialization with tools retriever and repository
- Agent metadata management
- History listing
- Query execution with callbacks
- Cleanup functionality
- Error handling
- Default repository creation
- ChatManager functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import AIMessage
from fivcplayground.app.utils import Chat, ChatManager
from fivcplayground.agents.types import AgentsRuntime, AgentsStatus, AgentsRuntimeMeta
from fivcplayground.agents.types.repositories import AgentsRuntimeRepository
from fivcplayground import tools


class TestChatInitialization:
    """Test Chat initialization."""

    def test_init_with_tools_retriever(self):
        """Test creating Chat with tools retriever uses default repository."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        manager = Chat(tools_retriever=mock_retriever)

        assert manager.tools_retriever is mock_retriever
        assert manager.runtime_repo is not None
        assert manager.monitor_manager is not None
        assert manager.running is False
        assert manager.id is None  # No metadata yet
        assert manager.runtime_meta is None

    def test_init_with_custom_repository(self):
        """Test creating Chat with custom repository."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        assert manager.tools_retriever is mock_retriever
        assert manager.runtime_repo is mock_repo
        assert manager.monitor_manager is not None

    def test_init_with_agent_runtime_meta(self):
        """Test creating Chat with agent runtime metadata."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        meta = AgentsRuntimeMeta(
            agent_id="my-custom-agent-id",
            agent_name="Test Agent",
            system_prompt="Test prompt",
            description="Test description",
        )

        manager = Chat(agent_runtime_meta=meta, tools_retriever=mock_retriever)

        assert manager.id == "my-custom-agent-id"
        assert manager.description == "Test description"
        assert manager.runtime_meta is meta

    def test_init_without_tools_retriever_raises_error(self):
        """Test that initialization without tools retriever raises assertion error."""
        with pytest.raises(AssertionError):
            Chat(tools_retriever=None)

    def test_is_running_property(self):
        """Test is_running property reflects running state."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        manager = Chat(tools_retriever=mock_retriever)

        assert manager.is_running is False

        manager.running = True
        assert manager.is_running is True

        manager.running = False
        assert manager.is_running is False


class TestChatAgentManagement:
    """Test agent ID and metadata management."""

    def test_id_property_returns_none_initially(self):
        """Test id property returns None when no metadata exists."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        manager = Chat(tools_retriever=mock_retriever)

        # Should be None initially
        assert manager.id is None

    def test_id_property_with_metadata(self):
        """Test id property returns agent_id from metadata."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        meta = AgentsRuntimeMeta(agent_id="test-agent-123", agent_name="Test Agent")

        manager = Chat(agent_runtime_meta=meta, tools_retriever=mock_retriever)

        assert manager.id == "test-agent-123"

    def test_description_property_with_metadata(self):
        """Test description property returns description from metadata."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        meta = AgentsRuntimeMeta(agent_id="test-agent", description="My test chat")

        manager = Chat(agent_runtime_meta=meta, tools_retriever=mock_retriever)

        assert manager.description == "My test chat"

    def test_description_falls_back_to_id(self):
        """Test description falls back to agent_id when no description."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        meta = AgentsRuntimeMeta(agent_id="test-agent")

        manager = Chat(agent_runtime_meta=meta, tools_retriever=mock_retriever)

        assert manager.description == "test-agent"


class TestChatHistory:
    """Test history listing functionality."""

    def test_list_history_returns_completed_runtimes(self):
        """Test list_history returns only completed agent runtimes with tool calls loaded."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        meta = AgentsRuntimeMeta(agent_id="test-agent")

        manager = Chat(
            agent_runtime_meta=meta,
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Mock runtime repository
        completed_runtime = AgentsRuntime(
            agent_id="test-agent",
            agent_run_id="run-123",
            status=AgentsStatus.COMPLETED,
        )
        pending_runtime = AgentsRuntime(
            agent_id="test-agent",
            agent_run_id="run-456",
            status=AgentsStatus.EXECUTING,
        )

        mock_repo.list_agent_runtimes = Mock(
            return_value=[completed_runtime, pending_runtime]
        )
        # Mock tool calls loading
        mock_repo.list_agent_runtime_tool_calls = Mock(return_value=[])

        history = manager.list_history()

        # Should only return completed runtime
        assert len(history) == 1
        assert history[0] is completed_runtime
        assert history[0].is_completed is True
        # Should have loaded tool calls for completed runtime
        mock_repo.list_agent_runtime_tool_calls.assert_called_once_with(
            "test-agent", "run-123"
        )

    def test_list_history_empty_when_no_metadata(self):
        """Test list_history returns empty list when no metadata."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        history = manager.list_history()

        assert history == []

    def test_list_history_empty_when_no_runtimes(self):
        """Test list_history returns empty list when no runtimes exist."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        meta = AgentsRuntimeMeta(agent_id="test-agent")

        manager = Chat(
            agent_runtime_meta=meta,
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        mock_repo.list_agent_runtimes = Mock(return_value=[])

        history = manager.list_history()

        assert history == []

    def test_list_history_loads_tool_calls_for_completed_runtimes(self):
        """Test list_history loads and attaches tool calls to completed runtimes."""
        from fivcplayground.agents.types import AgentsRuntimeToolCall
        from datetime import datetime

        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        meta = AgentsRuntimeMeta(agent_id="test-agent")

        manager = Chat(
            agent_runtime_meta=meta,
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Create completed runtime
        completed_runtime = AgentsRuntime(
            agent_id="test-agent",
            agent_run_id="run-123",
            status=AgentsStatus.COMPLETED,
        )

        # Create mock tool calls
        tool_call_1 = AgentsRuntimeToolCall(
            tool_use_id="tc-1",
            tool_name="calculator",
            tool_input={"expr": "2+2"},
            tool_result="4",
            status="success",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        tool_call_2 = AgentsRuntimeToolCall(
            tool_use_id="tc-2",
            tool_name="search",
            tool_input={"query": "test"},
            tool_result="results",
            status="success",
            started_at=datetime(2024, 1, 1, 10, 0, 1),
        )

        mock_repo.list_agent_runtimes = Mock(return_value=[completed_runtime])
        mock_repo.list_agent_runtime_tool_calls = Mock(
            return_value=[tool_call_2, tool_call_1]  # Unsorted order
        )

        history = manager.list_history()

        # Should have loaded and attached tool calls
        assert len(history) == 1
        assert len(history[0].tool_calls) == 2
        assert "tc-1" in history[0].tool_calls
        assert "tc-2" in history[0].tool_calls
        assert history[0].tool_calls["tc-1"] is tool_call_1
        assert history[0].tool_calls["tc-2"] is tool_call_2

        # Tool calls should be sorted by started_at
        tool_call_list = list(history[0].tool_calls.values())
        assert tool_call_list[0].tool_use_id == "tc-1"  # Earlier timestamp
        assert tool_call_list[1].tool_use_id == "tc-2"  # Later timestamp


class TestChatAsk:
    """Test query execution functionality."""

    @pytest.mark.asyncio
    async def test_ask_basic_execution(self):
        """Test basic ask execution flow."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_retriever.retrieve = Mock(return_value=[])  # Return empty list of tools
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        # Mock the agent runtime
        mock_agent = AsyncMock()
        mock_agent.run_async = AsyncMock(return_value="test response")
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.agent_id = "generated-agent-id"

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)
        mock_repo.update_agent = Mock()

        # Mock create_briefing_task and agent creator
        with patch(
            "fivcplayground.app.utils.chats.create_briefing_task"
        ) as mock_briefing_task, patch(
            "fivcplayground.app.utils.chats.agents.default_retriever.get"
        ) as mock_agent_creator_getter:
            # Mock the task to return a mock with run_async method that returns BaseMessage
            mock_task = Mock()
            mock_desc_msg = AIMessage(content="Agent description")
            mock_task.run_async = AsyncMock(return_value=mock_desc_msg)
            mock_briefing_task.return_value = mock_task

            # Mock the agent creator function
            mock_agent_creator = Mock(return_value=mock_agent)
            mock_agent_creator_getter.return_value = mock_agent_creator

            result = await manager.ask_async("test query")

        assert result == "test response"
        assert manager.running is False  # Should be reset after execution
        # Should save agent metadata on first query
        mock_repo.update_agent.assert_called_once()
        # Should have created metadata
        assert manager.runtime_meta is not None
        assert manager.runtime_meta.agent_id == "generated-agent-id"

    @pytest.mark.asyncio
    async def test_ask_with_existing_metadata(self):
        """Test ask execution with existing metadata doesn't recreate it."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_retriever.retrieve = Mock(return_value=[])  # Return empty list of tools
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_repo.list_agent_runtimes = Mock(return_value=[])  # Return empty list
        meta = AgentsRuntimeMeta(
            agent_id="existing-agent",
            agent_name="Existing Agent",
            system_prompt="Existing prompt",
        )

        manager = Chat(
            agent_runtime_meta=meta,
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Mock the agent runtime
        mock_agent = AsyncMock()
        mock_agent.run_async = AsyncMock(return_value="test response")

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)

        # Mock create_briefing_task and agent creator
        with patch(
            "fivcplayground.app.utils.chats.create_briefing_task"
        ) as mock_briefing_task, patch(
            "fivcplayground.app.utils.chats.agents.default_retriever.get"
        ) as mock_agent_creator_getter:
            # Mock the task to return a mock with run_async method
            mock_task = Mock()
            mock_task.run_async = AsyncMock(return_value="Agent description")
            mock_briefing_task.return_value = mock_task

            # Mock the agent creator function
            mock_agent_creator = Mock(return_value=mock_agent)
            mock_agent_creator_getter.return_value = mock_agent_creator

            result = await manager.ask_async("test query")

        assert result == "test response"
        # Should NOT save agent metadata (already exists)
        mock_repo.update_agent.assert_not_called()
        # Metadata should be unchanged
        assert manager.runtime_meta is meta

    @pytest.mark.asyncio
    async def test_ask_with_callback(self):
        """Test ask execution with on_event callback."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_retriever.retrieve = Mock(return_value=[])  # Return empty list of tools
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        mock_callback = Mock()
        mock_agent = AsyncMock()
        mock_agent.run_async = AsyncMock(return_value="response")
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.agent_id = "test-agent"

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)
        mock_repo.update_agent = Mock()

        # Mock create_briefing_task and agent creator
        with patch(
            "fivcplayground.app.utils.chats.create_briefing_task"
        ) as mock_briefing_task, patch(
            "fivcplayground.app.utils.chats.agents.default_retriever.get"
        ) as mock_agent_creator_getter:
            # Mock the task to return a mock with run_async method that returns BaseMessage
            mock_task = Mock()
            mock_desc_msg = AIMessage(content="Agent description")
            mock_task.run_async = AsyncMock(return_value=mock_desc_msg)
            mock_briefing_task.return_value = mock_task

            # Mock the agent creator function
            mock_agent_creator = Mock(return_value=mock_agent)
            mock_agent_creator_getter.return_value = mock_agent_creator

            await manager.ask_async("query", on_event=mock_callback)

        # Verify callback was passed to create_agent_runtime
        call_kwargs = manager.monitor_manager.create_agent_runtime.call_args[1]
        assert call_kwargs["on_event"] is mock_callback

    @pytest.mark.asyncio
    async def test_ask_raises_error_when_already_running(self):
        """Test ask raises ValueError when agent is already running."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        manager = Chat(tools_retriever=mock_retriever)
        manager.running = True

        with pytest.raises(ValueError) as exc_info:
            await manager.ask_async("test query")

        assert "already processing" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ask_resets_running_on_exception(self):
        """Test ask resets running flag even when exception occurs."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        mock_agent = AsyncMock()
        mock_agent.invoke_async = AsyncMock(side_effect=Exception("Test error"))
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.agent_id = "test-agent"

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)

        with pytest.raises(Exception):
            await manager.ask_async("query")

        # Running should be reset even after exception
        assert manager.running is False


class TestChatCleanup:
    """Test cleanup functionality."""

    def test_cleanup_deletes_agent_data(self):
        """Test cleanup deletes agent and all associated data."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        meta = AgentsRuntimeMeta(agent_id="test-agent")

        manager = Chat(
            agent_runtime_meta=meta,
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Cleanup
        manager.cleanup()

        # Should call delete_agent with the agent_id
        mock_repo.delete_agent.assert_called_once_with("test-agent")

    def test_cleanup_with_no_metadata_does_nothing(self):
        """Test cleanup does nothing when no metadata exists."""
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo = Mock(spec=AgentsRuntimeRepository)

        manager = Chat(agent_runtime_repo=mock_repo, tools_retriever=mock_retriever)

        # Cleanup
        manager.cleanup()

        # Should not call delete_agent when no metadata
        mock_repo.delete_agent.assert_not_called()


class TestChatManager:
    """Test ChatManager functionality."""

    def test_init_with_defaults(self):
        """Test ChatManager initialization with default settings."""
        manager = ChatManager()

        assert manager.runtime_repo is not None
        assert manager.tools_retriever is not None

    def test_init_with_custom_settings(self):
        """Test ChatManager initialization with custom settings."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)

        manager = ChatManager(
            agent_runtime_repo=mock_repo, tools_retriever=mock_retriever
        )

        assert manager.runtime_repo is mock_repo
        assert manager.tools_retriever is mock_retriever

    def test_list_chats_returns_chat_instances(self):
        """Test list_chats returns Chat instances for all agents."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)

        # Mock some agent metadata
        meta1 = AgentsRuntimeMeta(agent_id="agent-1", description="Chat 1")
        meta2 = AgentsRuntimeMeta(agent_id="agent-2", description="Chat 2")
        mock_repo.list_agents = Mock(return_value=[meta1, meta2])

        manager = ChatManager(
            agent_runtime_repo=mock_repo, tools_retriever=mock_retriever
        )

        chats = manager.list_chats()

        assert len(chats) == 2
        assert all(isinstance(chat, Chat) for chat in chats)
        assert chats[0].id == "agent-1"
        assert chats[1].id == "agent-2"
        assert chats[0].description == "Chat 1"
        assert chats[1].description == "Chat 2"

    def test_list_chats_empty(self):
        """Test list_chats returns empty list when no agents exist."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_repo.list_agents = Mock(return_value=[])

        manager = ChatManager(
            agent_runtime_repo=mock_repo, tools_retriever=mock_retriever
        )

        chats = manager.list_chats()

        assert chats == []

    def test_add_chat_creates_new_chat(self):
        """Test add_chat creates a new Chat instance."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)

        manager = ChatManager(
            agent_runtime_repo=mock_repo, tools_retriever=mock_retriever
        )

        chat = manager.add_chat()

        assert isinstance(chat, Chat)
        assert chat.runtime_repo is mock_repo
        assert chat.tools_retriever is mock_retriever
        assert chat.id is None  # No metadata yet

    def test_add_chat_creates_independent_instances(self):
        """Test add_chat creates independent Chat instances."""
        manager = ChatManager()

        chat1 = manager.add_chat()
        chat2 = manager.add_chat()

        assert chat1 is not chat2
        assert chat1.runtime_repo is chat2.runtime_repo  # Shared repo
        assert chat1.tools_retriever is chat2.tools_retriever  # Shared tools


class TestAgentExecutionMethodRegression:
    """Regression tests for agent execution method.

    These tests ensure that the agent execution uses the correct method (run_async)
    and not invoke_async, which was causing AttributeError in the Streamlit app.

    Issue: agent.invoke_async() was being called but agents have run_async() method
    """

    @pytest.mark.asyncio
    async def test_agent_execution_uses_run_async_not_invoke_async(self):
        """Regression test: Verify agent execution uses run_async method."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)
        mock_retriever.retrieve = Mock(return_value=[])  # Return empty list of tools

        manager = Chat(
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Create a mock agent with run_async method (correct)
        mock_agent = AsyncMock()
        mock_agent.run_async = AsyncMock(return_value="agent response")
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.agent_id = "test-agent-id"

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)
        mock_repo.update_agent = Mock()

        # Mock create_briefing_task and agent creator
        with patch(
            "fivcplayground.app.utils.chats.create_briefing_task"
        ) as mock_briefing_task, patch(
            "fivcplayground.app.utils.chats.agents.default_retriever.get"
        ) as mock_agent_creator_getter:
            mock_task = Mock()
            mock_desc_msg = AIMessage(content="Agent description")
            mock_task.run_async = AsyncMock(return_value=mock_desc_msg)
            mock_briefing_task.return_value = mock_task

            # Mock the agent creator function
            mock_agent_creator = Mock(return_value=mock_agent)
            mock_agent_creator_getter.return_value = mock_agent_creator

            # This should work without AttributeError
            result = await manager.ask_async("test query")

        # Verify run_async was called (not invoke_async)
        mock_agent.run_async.assert_called_once_with("test query")
        assert result == "agent response"

    @pytest.mark.asyncio
    async def test_agent_without_run_async_raises_error(self):
        """Regression test: Verify error if agent doesn't have run_async method."""
        mock_repo = Mock(spec=AgentsRuntimeRepository)
        mock_retriever = Mock(spec=tools.ToolsRetriever)

        manager = Chat(
            agent_runtime_repo=mock_repo,
            tools_retriever=mock_retriever,
        )

        # Create a mock agent WITHOUT run_async method (incorrect)
        mock_agent = Mock()
        # Don't set run_async - this should cause an error
        mock_agent.name = "TestAgent"
        mock_agent.system_prompt = "Test prompt"
        mock_agent.agent_id = "test-agent-id"

        manager.monitor_manager.create_agent_runtime = Mock(return_value=mock_agent)

        # Mock create_briefing_task
        with patch(
            "fivcplayground.app.utils.chats.create_briefing_task"
        ) as mock_briefing_task:
            mock_task = Mock()
            mock_task.run_async = AsyncMock(return_value="Agent description")
            mock_briefing_task.return_value = mock_task

            # This should raise an error because run_async is not available
            with pytest.raises((AttributeError, TypeError)):
                await manager.ask_async("test query")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
