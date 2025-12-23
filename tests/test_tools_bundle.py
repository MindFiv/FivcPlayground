#!/usr/bin/env python3
"""
Tests for the ToolBundle class.

ToolBundle is an MCP (Model Context Protocol) tools bundle that wraps
MCP server connections and provides async loading of tools.
"""

import pytest
from unittest.mock import Mock, patch

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.backends.langchain.tools import LangchainToolBundle
from fivcplayground.backends.strands.tools import StrandsToolBundle, StrandsTool

# Use both implementations - tests will run with whichever backend is active
# For now, we'll test both implementations
ToolBundleImpls = [LangchainToolBundle, StrandsToolBundle]


class TestToolsBundleInit:
    """Test ToolBundle initialization."""

    @pytest.mark.parametrize("ToolBundleImpl", ToolBundleImpls)
    def test_init_with_command_config(self, ToolBundleImpl):
        """Test ToolBundle initialization with command-based MCP config."""
        tool_config = ToolConfig(
            id="test_bundle",
            description="Test bundle",
            transport="stdio",
            command="python",
            args=["-m", "mcp_server"],
        )
        bundle = ToolBundleImpl(tool_config)

        # Use Tool interface to get tool name
        assert bundle.name == "test_bundle"
        # Check that config is stored
        assert bundle._tool_config == tool_config

    @pytest.mark.parametrize("ToolBundleImpl", ToolBundleImpls)
    def test_init_with_url_config(self, ToolBundleImpl):
        """Test ToolBundle initialization with URL-based MCP config."""
        tool_config = ToolConfig(
            id="test_bundle",
            description="Test bundle",
            transport="sse",
            url="http://localhost:8000/sse",
        )
        bundle = ToolBundleImpl(tool_config)

        # Use Tool interface to get tool name
        assert bundle.name == "test_bundle"
        # Check that config is stored
        assert bundle._tool_config == tool_config

    @pytest.mark.parametrize("ToolBundleImpl", ToolBundleImpls)
    def test_bundle_has_tool_name_attribute(self, ToolBundleImpl):
        """Test that ToolBundle has a name attribute."""
        tool_config = ToolConfig(
            id="my_bundle",
            description="My bundle",
            transport="stdio",
            command="python",
        )
        bundle = ToolBundleImpl(tool_config)

        # Both backends use .name property (from Tool interface)
        assert hasattr(bundle, "name")
        assert bundle.name == "my_bundle"


class TestToolsBundleAsync:
    """Test ToolBundle async loading via setup() method."""

    @pytest.mark.asyncio
    async def test_setup_with_command_config(self):
        """Test setup() with command-based config (Strands only)."""
        # Only test with Strands backend since LangChain uses different setup
        tool_config = ToolConfig(
            id="test_bundle",
            description="Test bundle",
            transport="stdio",
            command="python",
            args=["-m", "mcp_server"],
        )
        bundle = StrandsToolBundle(tool_config)

        # Mock the MCPClient and tools
        mock_tool = Mock()
        mock_tool.tool_name = "test_tool"

        with patch(
            "fivcplayground.backends.strands.tools.MCPClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.list_tools_sync.return_value = [mock_tool]
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client

            context = bundle.setup()
            async with context as tools:
                assert len(tools) == 1
                # Verify that the tool is wrapped in StrandsTool
                assert isinstance(tools[0], StrandsTool)
                assert tools[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_setup_with_url_config(self):
        """Test setup() with URL-based config (Strands only)."""
        # Only test with Strands backend since LangChain uses different setup
        tool_config = ToolConfig(
            id="test_bundle",
            description="Test bundle",
            transport="sse",
            url="http://localhost:8000/sse",
        )
        bundle = StrandsToolBundle(tool_config)

        # Mock the MCPClient and tools
        mock_tool = Mock()
        mock_tool.tool_name = "test_tool"

        with patch(
            "fivcplayground.backends.strands.tools.MCPClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.list_tools_sync.return_value = [mock_tool]
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client

            context = bundle.setup()
            async with context as tools:
                assert len(tools) == 1
                # Verify that the tool is wrapped in StrandsTool
                assert isinstance(tools[0], StrandsTool)
                assert tools[0].name == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
