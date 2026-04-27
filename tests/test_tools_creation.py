"""
Tests for tool creation functions in fivcplayground.tools module.

Tests verify:
- create_tool_retriever_async with various configurations
- Error handling for missing dependencies
"""

from unittest.mock import Mock, patch

import pytest
from fivcplayground.backends.strands.tools import StrandsToolBackend
from fivcplayground.tools import (
    create_tool_retriever_async,
)


class TestCreateToolRetriever:
    """Test create_tool_retriever_async function."""

    @pytest.mark.asyncio
    async def test_create_tool_retriever_requires_backend(self):
        """Test that create_tool_retriever_async requires tool_backend parameter."""
        with pytest.raises(RuntimeError, match="tool_backend is required"):
            await create_tool_retriever_async(
                tool_backend=None,
                embedding_config_repository=None,
            )

    @pytest.mark.asyncio
    async def test_create_tool_retriever_default(self):
        """Test creating tool retriever with default settings."""
        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                retriever = await create_tool_retriever_async(
                    tool_backend=StrandsToolBackend(),
                    embedding_config_repository=mock_embedding_repo,
                    tool_config_repository=mock_tool_repo,
                )

                assert retriever == mock_retriever
                mock_retriever_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_retriever_with_builtin_tools(self):
        """Test creating tool retriever with builtin tools passed explicitly."""
        from fivcplayground.tools import create_builtin_tools_async

        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                # Create builtin tools explicitly
                backend = StrandsToolBackend()
                builtin_tools = await create_builtin_tools_async(
                    tool_backend=backend,
                    raise_exception=False,
                )

                retriever = await create_tool_retriever_async(
                    tool_backend=backend,
                    tools=builtin_tools,
                    embedding_config_repository=mock_embedding_repo,
                    tool_config_repository=mock_tool_repo,
                )

                assert retriever == mock_retriever
                # Verify ToolRetriever was called with tools
                call_kwargs = mock_retriever_class.call_args[1]
                assert "tools" in call_kwargs
                assert len(call_kwargs["tools"]) >= 2  # clock and calculator

    @pytest.mark.asyncio
    async def test_create_tool_retriever_custom_embedding_config(self):
        """Test creating tool retriever with custom embedding config."""
        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                retriever = await create_tool_retriever_async(
                    tool_backend=StrandsToolBackend(),
                    embedding_config_repository=mock_embedding_repo,
                    tool_config_repository=mock_tool_repo,
                    embedding_config_id="custom",
                )

                assert retriever == mock_retriever
                # Verify create_embedding_db_async was called with the correct parameters
                mock_create_db.assert_called_once()
                call_kwargs = mock_create_db.call_args[1]
                assert call_kwargs["embedding_config_repository"] == mock_embedding_repo
                assert call_kwargs["embedding_config_id"] == "custom"

    @pytest.mark.asyncio
    async def test_create_tool_retriever_adds_self(self):
        """Test that tool retriever is created successfully."""
        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever.to_tool = Mock(return_value=Mock(name="tool_retriever"))
                mock_retriever_class.return_value = mock_retriever

                retriever = await create_tool_retriever_async(
                    tool_backend=StrandsToolBackend(),
                    embedding_config_repository=mock_embedding_repo,
                    tool_config_repository=mock_tool_repo,
                )

                # Verify ToolRetriever was created
                assert retriever == mock_retriever
                mock_retriever_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_retriever_builtin_tools_loaded(self):
        """Test that builtin tools can be passed to create_tool_retriever_async."""
        from fivcplayground.tools import create_builtin_tools_async

        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.tools = []
                mock_retriever_class.return_value = mock_retriever

                # Create builtin tools explicitly
                backend = StrandsToolBackend()
                builtin_tools = await create_builtin_tools_async(
                    tool_backend=backend,
                    raise_exception=False,
                )

                retriever = await create_tool_retriever_async(
                    tool_backend=backend,
                    tools=builtin_tools,
                    embedding_config_repository=mock_embedding_repo,
                    tool_config_repository=mock_tool_repo,
                )

                # Verify ToolRetriever was created with builtin tools
                assert retriever == mock_retriever
                # Verify ToolRetriever was called with tools containing builtin tools
                call_kwargs = mock_retriever_class.call_args[1]
                assert "tools" in call_kwargs
                assert len(call_kwargs["tools"]) >= 2  # clock and calculator
