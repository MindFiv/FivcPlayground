"""Integration tests for skill dynamic tool loading system."""

from unittest.mock import AsyncMock, Mock

import pytest

from fivcplayground.agents import AgentRunToolSpan
from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.repositories import SkillConfigRepository


def _make_mock_skill_config_repo(skills: list[SkillConfig]) -> SkillConfigRepository:
    """Create a mock SkillConfigRepository."""
    repo = Mock(spec=SkillConfigRepository)
    repo.list_skill_configs_async = AsyncMock(return_value=skills)
    repo.get_skill_config_async = AsyncMock(
        side_effect=lambda sid: next((s for s in skills if s.id == sid), None)
    )
    return repo


class TestSkillDynamicToolLoadingIntegration:
    """Integration tests for skill-based dynamic tool loading."""

    @pytest.mark.asyncio
    async def test_tool_span_register_tools_pattern(self):
        """Test the tool registration pattern used in skill callbacks."""
        # Create mock tool retriever
        mock_tool_retriever = AsyncMock()

        # Create mock tools
        tool1 = Mock()
        tool1.name = "tool1"
        tool2 = Mock()
        tool2.name = "tool2"

        mock_tool_retriever.get_tool_async = AsyncMock(
            side_effect=lambda name: {"tool1": tool1, "tool2": tool2}.get(name)
        )

        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Simulate skill callback pattern
        tools_loaded = []
        skill_tool_ids = ["tool1", "tool2"]
        for tool_id in skill_tool_ids:
            result = await span.register_tool_async(tool_id)
            tools_loaded.extend(result)

        # Verify tools were registered
        assert len(tools_loaded) == 2
        assert tool1 in tools_loaded
        assert tool2 in tools_loaded

    @pytest.mark.asyncio
    async def test_deduplication_pattern_across_skills(self):
        """Test tool deduplication pattern across multiple skill loads."""
        # Create mock tool retriever
        mock_tool_retriever = AsyncMock()

        # Create mock tools (some shared between skills)
        calc_tool = Mock()
        calc_tool.name = "calc"
        clock_tool = Mock()
        clock_tool.name = "clock"

        mock_tool_retriever.get_tool_async = AsyncMock(
            side_effect=lambda name: {
                "calc": calc_tool,
                "clock": clock_tool
            }.get(name)
        )

        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Simulate loading Skill A with ["calc", "clock"]
        for tool_id in ["calc", "clock"]:
            await span.register_tool_async(tool_id)

        # Verify both tools are in span
        assert len(span.tools) == 2

        # Simulate loading Skill B with ["calc"] (shared tool)
        result = await span.register_tool_async("calc")

        # calc should be deduplicated - not added again
        assert len(result) == 0  # Already registered
        assert len(span.tools) == 2  # Still only 2 tools in span

    @pytest.mark.asyncio
    async def test_tool_span_cleanup_pattern(self):
        """Test context manager cleanup for tool span without retriever."""
        # Create a span without tool_retriever to avoid calling get_tools_async
        span = AgentRunToolSpan(tool_retriever=None)

        tool = Mock()
        tool.name = "test_tool"
        # Manual registration before context manager
        await span.register_tool_async(tool)
        assert len(span.tools) == 1

        # Exit context (should cleanup)
        async with span:
            pass

        # After exit, should be empty
        assert len(span._tool_loaded) == 0
        assert len(span._tool_loaded_expanded) == 0
        assert len(span._tool_contexts) == 0

    @pytest.mark.asyncio
    async def test_empty_tool_list_handling(self):
        """Test handling skill with empty or None tool_ids."""
        mock_tool_retriever = AsyncMock()
        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Empty list
        tool_ids_empty = []
        registered_tools = []
        for tool_id in tool_ids_empty:
            result = await span.register_tool_async(tool_id)
            registered_tools.extend(result)

        assert len(registered_tools) == 0
        assert len(span.tools) == 0

    @pytest.mark.asyncio
    async def test_callback_integration_pattern(self):
        """Test the full callback integration pattern."""
        # Setup
        skill = SkillConfig(
            id="test-skill",
            description="Test",
            tool_ids=["t1", "t2"]
        )

        mock_tool_retriever = AsyncMock()
        t1 = Mock()
        t1.name = "t1"
        t2 = Mock()
        t2.name = "t2"

        mock_tool_retriever.get_tool_async = AsyncMock(
            side_effect=lambda name: {"t1": t1, "t2": t2}.get(name)
        )

        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Simulate callback pattern: when skill is loaded, load its tools
        async def skill_callback(skill_config):
            for tool_id in skill_config.tool_ids or []:
                await span.register_tool_async(tool_id)

        # Execute callback
        await skill_callback(skill)

        # Verify all skill tools were registered
        assert len(span.tools) == 2
        tool_names = {t.name for t in span.tools}
        assert tool_names == {"t1", "t2"}

    @pytest.mark.asyncio
    async def test_nonexistent_tool_handling(self):
        """Test handling when tool doesn't exist."""
        mock_tool_retriever = AsyncMock()
        mock_tool_retriever.get_tool_async = AsyncMock(return_value=None)

        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Try to register nonexistent tool
        result = await span.register_tool_async("does_not_exist")

        # Should return empty list
        assert len(result) == 0
        assert len(span.tools) == 0

    @pytest.mark.asyncio
    async def test_callback_with_all_patterns_combined(self):
        """Test complete callback flow with all patterns combined."""
        # Multiple skills, some with overlapping tools
        skill_a = SkillConfig(id="skill-a", description="A", tool_ids=["common", "unique_a"])
        skill_b = SkillConfig(id="skill-b", description="B", tool_ids=["common", "unique_b"])

        mock_tool_retriever = AsyncMock()
        common = Mock()
        common.name = "common"
        unique_a = Mock()
        unique_a.name = "unique_a"
        unique_b = Mock()
        unique_b.name = "unique_b"

        mock_tool_retriever.get_tool_async = AsyncMock(
            side_effect=lambda name: {
                "common": common,
                "unique_a": unique_a,
                "unique_b": unique_b,
            }.get(name)
        )

        span = AgentRunToolSpan(tool_retriever=mock_tool_retriever)

        # Load skill A
        for tool_id in skill_a.tool_ids or []:
            await span.register_tool_async(tool_id)

        # Load skill B
        for tool_id in skill_b.tool_ids or []:
            await span.register_tool_async(tool_id)

        # Verify deduplication: 3 unique tools total
        assert len(span.tools) == 3
        tool_names = {t.name for t in span.tools}
        assert tool_names == {"common", "unique_a", "unique_b"}
