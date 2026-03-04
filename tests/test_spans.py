"""Tests for AgentRunToolSpan and register_tool_async() method."""

from unittest.mock import AsyncMock, Mock

import pytest

from fivcplayground.agents.types.spans import AgentRunToolSpan
from fivcplayground.tools import ToolBundle


class TestRegisterToolAsync:
    """Test register_tool_async() method."""

    @pytest.mark.asyncio
    async def test_register_single_tool(self):
        """Test registering a single Tool object."""
        span = AgentRunToolSpan()
        tool = Mock()
        tool.name = "test_tool"

        result = await span.register_tool_async(tool)

        assert len(result) == 1
        assert result[0].name == "test_tool"
        assert "test_tool" in span._tool_loaded
        assert "test_tool" in span._tool_loaded_expanded

    @pytest.mark.asyncio
    async def test_register_tool_bundle(self):
        """Test registering a ToolBundle."""
        bundle_tool_1 = Mock()
        bundle_tool_1.name = "bundle_tool_1"
        bundle_tool_2 = Mock()
        bundle_tool_2.name = "bundle_tool_2"

        bundle = Mock(spec=ToolBundle)
        bundle.name = "test_bundle"
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = [bundle_tool_1, bundle_tool_2]
        mock_context.__aexit__.return_value = None
        bundle.setup = Mock(return_value=mock_context)

        span = AgentRunToolSpan()
        result = await span.register_tool_async(bundle)

        assert len(result) == 2
        assert result[0].name == "bundle_tool_1"
        assert result[1].name == "bundle_tool_2"
        assert "test_bundle" in span._tool_loaded
        assert "bundle_tool_1" in span._tool_loaded_expanded
        assert "bundle_tool_2" in span._tool_loaded_expanded

    @pytest.mark.asyncio
    async def test_register_tool_deduplication(self):
        """Test that registering same tool twice returns empty list."""
        span = AgentRunToolSpan()
        tool = Mock()
        tool.name = "unique_tool"

        # First registration
        result1 = await span.register_tool_async(tool)
        assert len(result1) == 1

        # Second registration of same tool
        result2 = await span.register_tool_async(tool)
        assert len(result2) == 0

    @pytest.mark.asyncio
    async def test_register_tool_by_name_without_retriever(self):
        """Test registering tool by name without retriever returns empty list."""
        span = AgentRunToolSpan()

        result = await span.register_tool_async("nonexistent_tool")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_register_multiple_tools(self):
        """Test registering multiple tools sequentially."""
        span = AgentRunToolSpan()
        tool1 = Mock()
        tool1.name = "tool_1"
        tool2 = Mock()
        tool2.name = "tool_2"
        tool3 = Mock()
        tool3.name = "tool_3"

        result1 = await span.register_tool_async(tool1)
        result2 = await span.register_tool_async(tool2)
        result3 = await span.register_tool_async(tool3)

        assert len(result1) == 1
        assert len(result2) == 1
        assert len(result3) == 1
        assert len(span.tools) == 3

    @pytest.mark.asyncio
    async def test_tools_property_returns_all_expanded_tools(self):
        """Test that tools property returns all expanded tools."""
        bundle_tool_1 = Mock()
        bundle_tool_1.name = "bundle_tool_1"
        bundle_tool_2 = Mock()
        bundle_tool_2.name = "bundle_tool_2"

        bundle = Mock(spec=ToolBundle)
        bundle.name = "multi_bundle"
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = [bundle_tool_1, bundle_tool_2]
        mock_context.__aexit__.return_value = None
        bundle.setup = Mock(return_value=mock_context)

        span = AgentRunToolSpan()
        tool = Mock()
        tool.name = "single_tool"

        await span.register_tool_async(tool)
        await span.register_tool_async(bundle)

        all_tools = span.tools
        assert len(all_tools) == 3
        tool_names = {t.name for t in all_tools}
        assert tool_names == {"single_tool", "bundle_tool_1", "bundle_tool_2"}

    @pytest.mark.asyncio
    async def test_context_manager_expands_tools(self):
        """Test context manager properly expands tools."""
        span = AgentRunToolSpan()

        async with span as span_ctx:
            # After entering context without explicit tool_ids, span should be ready
            assert span_ctx is span
            # Since no tool_retriever, tools list should be empty
            assert len(span_ctx.tools) == 0

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test context manager cleans up resources on exit."""
        span = AgentRunToolSpan()
        tool = Mock()
        tool.name = "cleanup_test"
        await span.register_tool_async(tool)

        assert len(span._tool_loaded) == 1
        assert len(span._tool_loaded_expanded) == 1

        async with span:
            pass

        # After exiting, should be cleaned up
        assert len(span._tool_loaded) == 0
        assert len(span._tool_loaded_expanded) == 0
        assert len(span._tool_contexts) == 0

    @pytest.mark.asyncio
    async def test_register_tool_bundle_preserves_deduplication(self):
        """Test deduplication across bundle tools."""
        bundle_tool_1 = Mock()
        bundle_tool_1.name = "bundle_tool_1"
        bundle_tool_2 = Mock()
        bundle_tool_2.name = "bundle_tool_2"

        bundle1 = Mock(spec=ToolBundle)
        bundle1.name = "bundle1"
        mock_context1 = AsyncMock()
        mock_context1.__aenter__.return_value = [bundle_tool_1, bundle_tool_2]
        mock_context1.__aexit__.return_value = None
        bundle1.setup = Mock(return_value=mock_context1)

        span = AgentRunToolSpan()

        # Register first bundle
        result1 = await span.register_tool_async(bundle1)
        assert len(result1) == 2

        # Try to register a tool with same name as bundle tool
        duplicate_tool = Mock()
        duplicate_tool.name = "bundle_tool_1"
        result2 = await span.register_tool_async(duplicate_tool)
        assert len(result2) == 0

    @pytest.mark.asyncio
    async def test_register_empty_tool_bundle(self):
        """Test registering an empty bundle."""
        empty_bundle = Mock(spec=ToolBundle)
        empty_bundle.name = "empty"
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = []
        mock_context.__aexit__.return_value = None
        empty_bundle.setup = Mock(return_value=mock_context)

        span = AgentRunToolSpan()

        result = await span.register_tool_async(empty_bundle)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_register_tool_async_order_preserved(self):
        """Test that multiple registrations preserve insertion order."""
        span = AgentRunToolSpan()

        for i in range(5):
            tool = Mock()
            tool.name = f"tool_{i}"
            await span.register_tool_async(tool)

        tools = span.tools
        names = [t.name for t in tools]
        expected = [f"tool_{i}" for i in range(5)]
        assert names == expected

