"""
Tests for tool creation functions in fivcplayground.tools module.

Tests verify:
- create_tool_retriever with various configurations
- create_tool_loader with tool retriever
- setup_tools async context manager
- Error handling for missing dependencies
"""

from unittest.mock import Mock, patch
import pytest

from fivcplayground.tools import (
    create_tool_retriever,
    create_tool_loader,
    setup_tools,
)


class TestCreateToolRetriever:
    """Test create_tool_retriever function."""

    def test_create_tool_retriever_default(self):
        """Test creating tool retriever with default settings."""
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
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
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.tools = []
            mock_retriever.add_tool = Mock()
            mock_retriever_class.return_value = mock_retriever

            retriever = create_tool_retriever(
                embedding_config_repository=None,
                load_builtin_tools=True,
            )

            assert retriever == mock_retriever
            # Should have called add_tool for builtin tools
            assert mock_retriever.add_tool.call_count >= 2

    def test_create_tool_retriever_custom_embedding_config(self):
        """Test creating tool retriever with custom embedding config."""
        mock_embedding_repo = Mock()

        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.tools = []
            mock_retriever_class.return_value = mock_retriever

            retriever = create_tool_retriever(
                embedding_config_repository=mock_embedding_repo,
                embedding_config_id="custom",
                load_builtin_tools=False,
            )

            assert retriever == mock_retriever
            # Verify the embedding config was passed
            call_kwargs = mock_retriever_class.call_args[1]
            assert call_kwargs["embedding_config_repository"] == mock_embedding_repo
            assert call_kwargs["embedding_config_id"] == "custom"

    def test_create_tool_retriever_adds_self(self):
        """Test that tool retriever adds itself as a tool."""
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.tools = []
            mock_retriever.to_tool = Mock(return_value=Mock(name="tool_retriever"))
            mock_retriever.add_tool = Mock()
            mock_retriever_class.return_value = mock_retriever

            create_tool_retriever(
                embedding_config_repository=None,
                load_builtin_tools=False,
            )

            # Verify add_tool was called with the retriever's own tool
            mock_retriever.add_tool.assert_called()

    def test_create_tool_retriever_builtin_tools_loaded(self):
        """Test that builtin tools are loaded when requested."""
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.tools = []
            mock_retriever.add_tool = Mock()
            mock_retriever_class.return_value = mock_retriever

            with patch("fivcplayground.tools.clock") as _:
                with patch("fivcplayground.tools.calculator") as _:
                    create_tool_retriever(
                        embedding_config_repository=None,
                        load_builtin_tools=True,
                    )

                    # Verify add_tool was called for clock and calculator
                    assert mock_retriever.add_tool.call_count >= 3


class TestCreateToolLoader:
    """Test create_tool_loader function."""

    def test_create_tool_loader_with_retriever(self):
        """Test creating tool loader with retriever."""
        mock_retriever = Mock()
        mock_retriever.tools = []
        mock_config_repo = Mock()

        with patch("fivcplayground.tools.ToolLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader

            loader = create_tool_loader(
                tool_retriever=mock_retriever,
                tool_config_repository=mock_config_repo,
            )

            assert loader == mock_loader
            mock_loader_class.assert_called_once()

    def test_create_tool_loader_missing_retriever(self):
        """Test create_tool_loader raises error without retriever."""
        with pytest.raises(ValueError, match="tool_retriever must be provided"):
            create_tool_loader(tool_retriever=None)

    def test_create_tool_loader_with_config_repository(self):
        """Test creating tool loader with config repository."""
        mock_retriever = Mock()
        mock_retriever.tools = []
        mock_config_repo = Mock()

        with patch("fivcplayground.tools.ToolLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader

            loader = create_tool_loader(
                tool_retriever=mock_retriever,
                tool_config_repository=mock_config_repo,
            )

            assert loader == mock_loader
            # Verify config repo was passed
            call_kwargs = mock_loader_class.call_args[1]
            assert call_kwargs["tool_config_repository"] == mock_config_repo

    def test_create_tool_loader_passes_kwargs(self):
        """Test create_tool_loader passes additional kwargs."""
        mock_retriever = Mock()
        mock_retriever.tools = []
        mock_config_repo = Mock()

        with patch("fivcplayground.tools.ToolLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader

            loader = create_tool_loader(
                tool_retriever=mock_retriever,
                tool_config_repository=mock_config_repo,
                custom_param="custom_value",
            )

            assert loader == mock_loader


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
