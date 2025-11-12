#!/usr/bin/env python3
"""
Tests for the tools/types/loaders module.

This module contains tests for the ToolsLoader class which manages loading
tools from MCP servers and registering them with a ToolsRetriever.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fivcplayground import __backend__
from fivcplayground.tools.types.loaders import ToolsLoader
from fivcplayground.tools.types.retrievers import ToolsRetriever


def create_mock_tool(name: str, description: str):
    """Create a mock tool with correct attributes based on the current backend."""
    tool = Mock()
    if __backend__ == "langchain":
        tool.name = name
        tool.description = description
    else:  # strands
        tool.tool_name = name
        tool.tool_spec = {"description": description}
    return tool


class TestToolsLoaderInit:
    """Test ToolsLoader initialization."""

    def test_init_with_retriever(self):
        """Test initialization with a ToolsRetriever."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            assert loader.tools_retriever == mock_retriever
            assert loader.tools_bundles == {}
            assert loader.config is not None
        finally:
            os.unlink(config_path)

    def test_init_without_retriever_raises_assertion(self):
        """Test that initialization without retriever raises AssertionError."""
        with pytest.raises(AssertionError):
            ToolsLoader(tools_retriever=None)

    def test_init_with_default_config_file(self):
        """Test initialization with default config file from environment."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "mcp.yaml")
            with open(config_path, "w") as f:
                f.write("test_server:\n  command: python\n  args:\n    - test.py\n")

            # Set environment variable
            old_env = os.environ.get("MCP_FILE")
            try:
                os.environ["MCP_FILE"] = config_path
                loader = ToolsLoader(tools_retriever=mock_retriever)
                assert loader.config is not None
            finally:
                if old_env is not None:
                    os.environ["MCP_FILE"] = old_env
                else:
                    os.environ.pop("MCP_FILE", None)


class TestToolsLoaderLoad:
    """Test ToolsLoader load methods."""

    def test_load_calls_load_async(self):
        """Test that load() calls load_async()."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            with patch.object(
                loader, "load_async", new_callable=AsyncMock
            ) as mock_load_async:
                loader.load()
                mock_load_async.assert_called_once()
        finally:
            os.unlink(config_path)

    @pytest.mark.asyncio
    async def test_load_async_with_no_servers(self):
        """Test load_async with no configured servers."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")  # Empty config
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            await loader.load_async()

            # Should not call add if no servers
            mock_retriever.add.assert_not_called()
        finally:
            os.unlink(config_path)

    @pytest.mark.asyncio
    async def test_load_async_with_tools(self):
        """Test load_async successfully loads tools."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            # Mock the ToolsBundle to avoid actual MCP connections
            with patch(
                "fivcplayground.tools.types.loaders.ToolsBundle"
            ) as mock_bundle_class:
                mock_bundle = MagicMock()
                mock_bundle_class.return_value = mock_bundle

                # Create mock tools with correct attributes for current backend
                mock_tool1 = create_mock_tool("tool1", "Tool 1 description")
                mock_tool2 = create_mock_tool("tool2", "Tool 2 description")

                # Mock the async context manager
                mock_bundle.load_async.return_value.__aenter__.return_value = [
                    mock_tool1,
                    mock_tool2,
                ]
                mock_bundle.load_async.return_value.__aexit__.return_value = None

                await loader.load_async()

                # Verify bundle was added
                mock_retriever.add.assert_called_once()

                # Verify tools_bundles was updated
                assert "test_server" in loader.tools_bundles
                assert "tool1" in loader.tools_bundles["test_server"]
                assert "tool2" in loader.tools_bundles["test_server"]
        finally:
            os.unlink(config_path)

    @pytest.mark.asyncio
    async def test_load_async_handles_errors(self):
        """Test load_async handles errors gracefully."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            with patch(
                "fivcplayground.tools.types.loaders.ToolsBundle"
            ) as mock_bundle_class:
                # Make the bundle raise an error when loading
                mock_bundle_class.side_effect = Exception("Connection failed")

                # Should not raise, just continue
                await loader.load_async()

                # Should not call add if error occurred
                mock_retriever.add.assert_not_called()
        finally:
            os.unlink(config_path)


class TestToolsLoaderCleanup:
    """Test ToolsLoader cleanup method."""

    def test_cleanup_removes_all_tools(self):
        """Test cleanup removes all tracked bundles."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            # Simulate tools being loaded in bundles
            loader.tools_bundles = {"bundle1": {"tool1", "tool2"}, "bundle2": {"tool3"}}

            loader.cleanup()

            # Verify remove was called for each bundle (not each tool)
            assert mock_retriever.remove.call_count == 2
            # Verify the bundle names were passed to remove
            mock_retriever.remove.assert_any_call("bundle1")
            mock_retriever.remove.assert_any_call("bundle2")

            # Verify tools_bundles was cleared
            assert loader.tools_bundles == {}
        finally:
            os.unlink(config_path)

    def test_cleanup_with_no_tools(self):
        """Test cleanup with no tools loaded."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            loader.cleanup()

            # Should not call remove if no tools
            mock_retriever.remove.assert_not_called()
        finally:
            os.unlink(config_path)

    def test_cleanup_calls_remove_method(self):
        """Test that cleanup uses the remove() method with bundle names."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )
            loader.tools_bundles = {"bundle1": {"tool1"}}

            loader.cleanup()

            # Verify remove method was called with bundle name (not tool name)
            mock_retriever.remove.assert_called_once_with("bundle1")
        finally:
            os.unlink(config_path)


class TestToolsLoaderIncrementalUpdates:
    """Test ToolsLoader incremental bundle updates."""

    @pytest.mark.asyncio
    async def test_load_async_adds_new_bundles(self):
        """Test load_async adds new bundles."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("server1:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            # Create mock tools with correct attributes for current backend
            mock_tool1 = create_mock_tool("tool1", "Tool 1 description")

            with patch(
                "fivcplayground.tools.types.loaders.ToolsBundle"
            ) as mock_bundle_class:
                mock_bundle = MagicMock()
                mock_bundle_class.return_value = mock_bundle

                # Mock the async context manager
                mock_bundle.load_async.return_value.__aenter__.return_value = [
                    mock_tool1
                ]
                mock_bundle.load_async.return_value.__aexit__.return_value = None

                await loader.load_async()

                # Verify bundle was added
                assert "server1" in loader.tools_bundles
                assert "tool1" in loader.tools_bundles["server1"]
        finally:
            os.unlink(config_path)

    @pytest.mark.asyncio
    async def test_load_async_removes_old_bundles(self):
        """Test load_async removes bundles that are no longer configured."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("server1:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            # Simulate previously loaded bundle
            loader.tools_bundles = {"old_server": {"old_tool"}}

            with patch(
                "fivcplayground.tools.types.loaders.ToolsBundle"
            ) as mock_bundle_class:
                mock_bundle = MagicMock()
                mock_bundle_class.return_value = mock_bundle

                # Mock the async context manager to return empty list
                mock_bundle.load_async.return_value.__aenter__.return_value = []
                mock_bundle.load_async.return_value.__aexit__.return_value = None

                await loader.load_async()

                # Verify old bundle was removed by bundle name
                mock_retriever.remove.assert_called_once_with("old_server")
                assert "old_server" not in loader.tools_bundles
        finally:
            os.unlink(config_path)


class TestToolsLoaderPersistentConnections:
    """Test persistent MCP connections in ToolsLoader."""

    @pytest.mark.asyncio
    async def test_load_async_uses_async_with(self):
        """Test that load_async uses async with for proper session lifecycle."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            with patch(
                "fivcplayground.tools.types.loaders.ToolsBundle"
            ) as mock_bundle_class:
                mock_bundle = MagicMock()
                mock_bundle_class.return_value = mock_bundle

                # Mock get_tools to return the tool with correct attributes for current backend
                mock_tool = create_mock_tool("test_tool", "Test tool description")

                mock_bundle.load_async.return_value.__aenter__.return_value = [
                    mock_tool
                ]
                mock_bundle.load_async.return_value.__aexit__.return_value = None

                await loader.load_async()

                # Verify tools are loaded and registered
                assert "test_server" in loader.tools_bundles
                mock_retriever.add.assert_called_once()
        finally:
            os.unlink(config_path)

    @pytest.mark.asyncio
    async def test_cleanup_async_removes_tools(self):
        """Test that cleanup_async removes all tools and clears state."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            # Set up tools
            loader.tools_bundles = {
                "server1": {"tool1", "tool2"},
                "server2": {"tool3"},
            }

            await loader.cleanup_async()

            # Verify bundles were removed (2 bundles, not 3 tools)
            assert mock_retriever.remove.call_count == 2
            mock_retriever.remove.assert_any_call("server1")
            mock_retriever.remove.assert_any_call("server2")

            # Verify state was cleared
            assert loader.tools_bundles == {}
        finally:
            os.unlink(config_path)

    def test_cleanup_sync_wrapper(self):
        """Test that cleanup() synchronously calls cleanup_async()."""
        mock_retriever = Mock(spec=ToolsRetriever)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_server:\n  command: python\n  args:\n    - test.py\n")
            f.flush()
            config_path = f.name

        try:
            loader = ToolsLoader(
                tools_retriever=mock_retriever, config_file=config_path
            )

            with patch.object(
                loader, "cleanup_async", new_callable=AsyncMock
            ) as mock_cleanup_async:
                loader.cleanup()
                mock_cleanup_async.assert_called_once()
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__])
