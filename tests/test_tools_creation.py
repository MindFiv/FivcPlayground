"""
Tests for tool creation functions in fivcplayground.tools module.

Tests verify:
- create_tool_retriever with various configurations
- setup_tools async context manager
- Error handling for missing dependencies
"""

from unittest.mock import Mock, patch
import pytest

from fivcplayground.tools import (
    create_tool_retriever,
    setup_tools,
)


class TestCreateToolRetriever:
    """Test create_tool_retriever function."""

    def test_create_tool_retriever_default(self):
        """Test creating tool retriever with default settings."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    embedding_config_repository=None,
                    load_builtin_tools=False,
                )

                assert retriever == mock_retriever
                mock_retriever_class.assert_called_once()

    def test_create_tool_retriever_with_builtin_tools(self):
        """Test creating tool retriever with builtin tools."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever.add_tool = Mock()
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    embedding_config_repository=None,
                    load_builtin_tools=True,
                )

                assert retriever == mock_retriever
                # Builtin tools are now passed during initialization, not added via add_tool
                # So we just verify the retriever was created
                mock_retriever_class.assert_called_once()

    def test_create_tool_retriever_custom_embedding_config(self):
        """Test creating tool retriever with custom embedding config."""
        mock_embedding_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    embedding_config_repository=mock_embedding_repo,
                    embedding_config_id="custom",
                    load_builtin_tools=False,
                )

                assert retriever == mock_retriever
                # Verify create_embedding_db was called with the correct parameters
                mock_create_db.assert_called_once()
                call_kwargs = mock_create_db.call_args[1]
                assert call_kwargs["embedding_config_repository"] == mock_embedding_repo
                assert call_kwargs["embedding_config_id"] == "custom"

    def test_create_tool_retriever_adds_self(self):
        """Test that tool retriever is created successfully."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever.to_tool = Mock(return_value=Mock(name="tool_retriever"))
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    embedding_config_repository=None,
                    load_builtin_tools=False,
                )

                # Verify ToolRetriever was created
                assert retriever == mock_retriever
                mock_retriever_class.assert_called_once()

    def test_create_tool_retriever_builtin_tools_loaded(self):
        """Test that builtin tools are loaded when requested."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    embedding_config_repository=None,
                    load_builtin_tools=True,
                )

                # Verify ToolRetriever was created with builtin tools
                assert retriever == mock_retriever
                # Verify ToolRetriever was called with tool_list containing builtin tools
                call_kwargs = mock_retriever_class.call_args[1]
                assert "tool_list" in call_kwargs
                assert len(call_kwargs["tool_list"]) >= 2  # clock and calculator


class TestSetupTools:
    """Test setup_tools async context manager."""

    def test_setup_tools_is_callable(self):
        """Test that setup_tools is callable."""
        assert callable(setup_tools)

    def test_setup_tools_returns_async_context_manager(self):
        """Test that setup_tools returns an async context manager."""
        mock_tool = Mock()
        mock_tool.name = "tool"

        result = setup_tools([mock_tool])

        # Verify it has async context manager methods
        assert hasattr(result, "__aenter__")
        assert hasattr(result, "__aexit__")

    @pytest.mark.asyncio
    async def test_setup_tools_with_empty_list(self):
        """Test setup_tools with empty tool list."""
        async with setup_tools([]) as tools:
            assert isinstance(tools, list)
            assert len(tools) == 0

    @pytest.mark.asyncio
    async def test_setup_tools_with_regular_tools(self):
        """Test setup_tools with regular tools."""
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"

        async with setup_tools([mock_tool1, mock_tool2]) as tools:
            assert isinstance(tools, list)
            assert len(tools) == 2
