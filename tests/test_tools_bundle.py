#!/usr/bin/env python3
"""
Tests for the ToolsBundle class.

ToolsBundle is an MCP (Model Context Protocol) tools bundle that wraps
MCP server connections and provides async loading of tools.
"""

import pytest
from unittest.mock import Mock, patch

from fivcplayground import __backend__
from fivcplayground.tools.types.backends import ToolsBundle, get_tool_name


class TestToolsBundleInit:
    """Test ToolsBundle initialization."""

    def test_init_with_command_config(self):
        """Test ToolsBundle initialization with command-based MCP config."""
        conn = {
            "command": "python",
            "args": ["-m", "mcp_server"],
        }
        bundle = ToolsBundle("test_bundle", conn)

        # Use backend-agnostic function to get tool name
        assert get_tool_name(bundle) == "test_bundle"
        # Check that connection is stored (implementation-specific)
        if __backend__ == "strands":
            assert bundle._conn == conn
        else:  # langchain
            # In LangChain, _conn is set via object.__setattr__
            assert hasattr(bundle, "_conn")

    def test_init_with_url_config(self):
        """Test ToolsBundle initialization with URL-based MCP config."""
        conn = {
            "url": "http://localhost:8000/sse",
        }
        bundle = ToolsBundle("test_bundle", conn)

        # Use backend-agnostic function to get tool name
        assert get_tool_name(bundle) == "test_bundle"
        # Check that connection is stored (implementation-specific)
        if __backend__ == "strands":
            assert bundle._conn == conn
        else:  # langchain
            # In LangChain, _conn is set via object.__setattr__
            assert hasattr(bundle, "_conn")

    def test_bundle_has_tool_name_attribute(self):
        """Test that ToolsBundle has a tool_name attribute (or name for LangChain)."""
        conn = {"command": "python"}
        bundle = ToolsBundle("my_bundle", conn)

        # Check for backend-specific attributes
        if __backend__ == "strands":
            assert hasattr(bundle, "tool_name")
            assert bundle.tool_name == "my_bundle"
        else:  # langchain
            assert hasattr(bundle, "name")
            assert bundle.name == "my_bundle"

        # Also verify using backend-agnostic function
        assert get_tool_name(bundle) == "my_bundle"


class TestToolsBundleAsync:
    """Test ToolsBundle async loading."""

    @pytest.mark.skipif(
        __backend__ != "strands", reason="Only test with Strands backend"
    )
    @pytest.mark.asyncio
    async def test_load_async_with_command_config(self):
        """Test async loading with command-based config."""
        conn = {
            "command": "python",
            "args": ["-m", "mcp_server"],
        }
        bundle = ToolsBundle("test_bundle", conn)

        # Mock the MCPClient and tools
        mock_tool = Mock()
        mock_tool.tool_name = "test_tool"

        with patch(
            "fivcplayground.tools.types.backends.strands.MCPClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.list_tools_sync.return_value = [mock_tool]
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client

            async with bundle.load_async() as tools:
                assert len(tools) == 1
                assert tools[0] == mock_tool

    @pytest.mark.skipif(
        __backend__ != "strands", reason="Only test with Strands backend"
    )
    @pytest.mark.asyncio
    async def test_load_async_with_url_config(self):
        """Test async loading with URL-based config."""
        conn = {
            "url": "http://localhost:8000/sse",
        }
        bundle = ToolsBundle("test_bundle", conn)

        # Mock the MCPClient and tools
        mock_tool = Mock()
        mock_tool.tool_name = "test_tool"

        with patch(
            "fivcplayground.tools.types.backends.strands.MCPClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.list_tools_sync.return_value = [mock_tool]
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client

            async with bundle.load_async() as tools:
                assert len(tools) == 1
                assert tools[0] == mock_tool


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
