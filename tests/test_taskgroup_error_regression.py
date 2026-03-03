from unittest.mock import AsyncMock, Mock

import pytest
from fivcplayground.agents import AgentRunToolSpan
from fivcplayground.tools import ToolBundle


class TestAgentRunToolSpanListFlattening:
    """Test that AgentRunToolSpan properly flattens ToolBundle results."""

    @pytest.mark.asyncio
    async def test_agent_run_tool_span_flattens_tool_bundle_results(self):
        """Test that ToolBundle tools are flattened, not nested."""
        # Create mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool3 = Mock()
        mock_tool3.name = "tool3"

        # Create a mock ToolBundle that returns a list of tools via setup()
        mock_bundle = Mock(spec=ToolBundle)
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = [mock_tool1, mock_tool2]
        mock_context.__aexit__.return_value = None
        mock_bundle.setup = Mock(return_value=mock_context)

        # Create a mock tool retriever that returns a mix of regular tools and bundles
        mock_tool_retriever = AsyncMock()
        mock_tool_retriever.list_tools_async = AsyncMock(
            return_value=[mock_bundle, mock_tool3]
        )

        # Create AgentRunToolSpan with the mock tool retriever
        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        tool_span = await span.__aenter__()
        tools_expanded = tool_span.tools

        # Verify the result is properly flattened
        assert len(tools_expanded) == 3, f"Expected 3 tools, got {len(tools_expanded)}"
        assert tools_expanded[0] == mock_tool1
        assert tools_expanded[1] == mock_tool2
        assert tools_expanded[2] == mock_tool3

        # Verify no nested lists exist
        for tool in tools_expanded:
            assert not isinstance(
                tool, list
            ), f"Found nested list in tools_expanded: {tool}"

    @pytest.mark.asyncio
    async def test_agent_run_tool_span_handles_multiple_bundles(self):
        """Test AgentRunToolSpan with multiple ToolBundles."""
        # Create mock tools for bundle 1
        bundle1_tool1 = Mock()
        bundle1_tool1.name = "bundle1_tool1"
        bundle1_tool2 = Mock()
        bundle1_tool2.name = "bundle1_tool2"

        # Create mock tools for bundle 2
        bundle2_tool1 = Mock()
        bundle2_tool1.name = "bundle2_tool1"

        # Create mock bundles
        mock_bundle1 = Mock(spec=ToolBundle)
        mock_bundle2 = Mock(spec=ToolBundle)

        mock_context1 = AsyncMock()
        mock_context2 = AsyncMock()

        mock_context1.__aenter__.return_value = [bundle1_tool1, bundle1_tool2]
        mock_context1.__aexit__.return_value = None
        mock_context2.__aenter__.return_value = [bundle2_tool1]
        mock_context2.__aexit__.return_value = None

        mock_bundle1.setup = Mock(return_value=mock_context1)
        mock_bundle2.setup = Mock(return_value=mock_context2)

        # Create a mock tool retriever that returns multiple bundles
        mock_tool_retriever = AsyncMock()
        mock_tool_retriever.list_tools_async = AsyncMock(
            return_value=[mock_bundle1, mock_bundle2]
        )

        # Create AgentRunToolSpan with the mock tool retriever
        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        tool_span = await span.__aenter__()
        tools_expanded = tool_span.tools

        # Verify all tools are flattened
        assert len(tools_expanded) == 3
        assert tools_expanded[0] == bundle1_tool1
        assert tools_expanded[1] == bundle1_tool2
        assert tools_expanded[2] == bundle2_tool1

        # Verify no nested lists
        for tool in tools_expanded:
            assert not isinstance(tool, list)

    @pytest.mark.asyncio
    async def test_agent_run_tool_span_with_empty_bundle(self):
        """Test AgentRunToolSpan handles empty ToolBundle results."""
        mock_tool = Mock()
        mock_tool.name = "regular_tool"

        mock_bundle = Mock(spec=ToolBundle)
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = []
        mock_context.__aexit__.return_value = None
        mock_bundle.setup = Mock(return_value=mock_context)

        # Create a mock tool retriever that returns bundle and regular tool
        mock_tool_retriever = AsyncMock()
        mock_tool_retriever.list_tools_async = AsyncMock(
            return_value=[mock_bundle, mock_tool]
        )

        # Create AgentRunToolSpan with the mock tool retriever
        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        tool_span = await span.__aenter__()
        tools_expanded = tool_span.tools

        # Should have only the regular tool
        assert len(tools_expanded) == 1
        assert tools_expanded[0] == mock_tool


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
