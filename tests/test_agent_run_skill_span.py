"""
Unit tests for AgentRunSkillSpan context manager.

Tests the skill span lifecycle including:
- Skill ID parsing into paths vs IDs
- Skill path extraction
- Skill registration with tool callback
- Context manager lifecycle
"""

from unittest.mock import AsyncMock, MagicMock, call
import pytest

from fivcplayground.agents.types.spans import AgentRunSkillSpan, AgentRunToolSpan
from fivcplayground.skills import SkillConfig, SkillRetriever
from fivcplayground.tools import Tool


class TestAgentRunSkillSpan:
    """Test AgentRunSkillSpan context manager."""

    @pytest.mark.asyncio
    async def test_init_with_no_retriever(self):
        """Test initialization without skill retriever."""
        span = AgentRunSkillSpan(skill_retriever=None, skill_ids=["skill1"])

        assert span._skill_retriever is None
        assert span._skill_ids == ["skill1"]
        assert span._skill_parsed_paths == []
        assert span._skill_parsed_ids == []

    @pytest.mark.asyncio
    async def test_init_with_retriever(self):
        """Test initialization with skill retriever."""
        mock_retriever = MagicMock(spec=SkillRetriever)
        span = AgentRunSkillSpan(
            skill_retriever=mock_retriever, skill_ids=["skill1", "skill2"]
        )

        assert span._skill_retriever is mock_retriever
        assert span._skill_ids == ["skill1", "skill2"]

    @pytest.mark.asyncio
    async def test_aenter_no_retriever(self):
        """Test __aenter__ with no retriever returns self immediately."""
        span = AgentRunSkillSpan(skill_retriever=None, skill_ids=["skill1"])

        result = await span.__aenter__()

        assert result is span
        assert span._skill_parsed_paths == []
        assert span._skill_parsed_ids == []

    @pytest.mark.asyncio
    async def test_aenter_no_skill_ids(self):
        """Test __aenter__ with no skill_ids returns self immediately."""
        mock_retriever = MagicMock(spec=SkillRetriever)
        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=None)

        result = await span.__aenter__()

        assert result is span
        assert span._skill_parsed_paths == []
        assert span._skill_parsed_ids == []

    @pytest.mark.asyncio
    async def test_aenter_parses_skill_with_path(self):
        """Test __aenter__ correctly parses skills with path field."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        # Skill with path should go to _skill_parsed_paths
        skill_with_path = SkillConfig(
            id="skill1",
            description="Test skill",
            path="/path/to/skill",
        )
        mock_retriever.get_skill_async = AsyncMock(return_value=skill_with_path)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])

        await span.__aenter__()

        assert span._skill_parsed_paths == ["/path/to/skill"]
        assert span._skill_parsed_ids == []
        mock_retriever.get_skill_async.assert_called_once_with("skill1")

    @pytest.mark.asyncio
    async def test_aenter_parses_skill_without_path(self):
        """Test __aenter__ correctly parses skills without path field."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        # Skill without path should go to _skill_parsed_ids
        skill_without_path = SkillConfig(
            id="skill2",
            description="Test skill",
            instructions="Do something",
            tool_ids=["tool1"],
        )
        mock_retriever.get_skill_async = AsyncMock(return_value=skill_without_path)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill2"])

        await span.__aenter__()

        assert span._skill_parsed_paths == []
        assert span._skill_parsed_ids == ["skill2"]
        mock_retriever.get_skill_async.assert_called_once_with("skill2")

    @pytest.mark.asyncio
    async def test_aenter_parses_multiple_skills(self):
        """Test __aenter__ correctly parses multiple skills."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill1 = SkillConfig(
            id="skill1",
            description="Skill with path",
            path="/path/to/skill1",
        )
        skill2 = SkillConfig(
            id="skill2",
            description="Skill without path",
            tool_ids=["tool1"],
        )
        skill3 = SkillConfig(
            id="skill3",
            description="Another skill with path",
            path="/path/to/skill3",
        )

        async def mock_get_skill(sid):
            skills = {"skill1": skill1, "skill2": skill2, "skill3": skill3}
            return skills.get(sid)

        mock_retriever.get_skill_async = mock_get_skill

        span = AgentRunSkillSpan(
            skill_retriever=mock_retriever, skill_ids=["skill1", "skill2", "skill3"]
        )

        await span.__aenter__()

        assert span._skill_parsed_paths == ["/path/to/skill1", "/path/to/skill3"]
        assert span._skill_parsed_ids == ["skill2"]

    @pytest.mark.asyncio
    async def test_aenter_handles_nonexistent_skill(self):
        """Test __aenter__ skips skills that don't exist."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill1 = SkillConfig(
            id="skill1",
            description="Existing skill",
            path="/path/to/skill1",
        )

        async def mock_get_skill(sid):
            if sid == "skill1":
                return skill1
            return None

        mock_retriever.get_skill_async = mock_get_skill

        span = AgentRunSkillSpan(
            skill_retriever=mock_retriever,
            skill_ids=["skill1", "nonexistent", "skill2"],
        )

        await span.__aenter__()

        # Only skill1 should be parsed
        assert span._skill_parsed_paths == ["/path/to/skill1"]
        assert span._skill_parsed_ids == []

    @pytest.mark.asyncio
    async def test_aenter_clears_previous_state(self):
        """Test __aenter__ clears previous parsed state."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill = SkillConfig(
            id="skill1",
            description="Test skill",
            path="/new/path",
        )
        mock_retriever.get_skill_async = AsyncMock(return_value=skill)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])

        # Manually set some state
        span._skill_parsed_paths = ["/old/path1", "/old/path2"]
        span._skill_parsed_ids = ["old_id"]

        await span.__aenter__()

        # Should be cleared and only contain new parsed result
        assert span._skill_parsed_paths == ["/new/path"]
        assert span._skill_parsed_ids == []

    @pytest.mark.asyncio
    async def test_get_skill_paths(self):
        """Test get_skill_paths returns parsed paths."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill = SkillConfig(
            id="skill1",
            description="Test skill",
            path="/path/to/skill",
        )
        mock_retriever.get_skill_async = AsyncMock(return_value=skill)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])

        await span.__aenter__()
        paths = span.get_skill_paths()

        assert paths == ["/path/to/skill"]

    @pytest.mark.asyncio
    async def test_get_skill_ids(self):
        """Test get_skill_ids returns parsed IDs (not original)."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill = SkillConfig(
            id="skill2",
            description="Test skill",
            tool_ids=["tool1"],
        )
        mock_retriever.get_skill_async = AsyncMock(return_value=skill)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill2"])

        await span.__aenter__()
        ids = span.get_skill_ids()

        # Should return parsed IDs, not original skill_ids
        assert ids == ["skill2"]
        assert ids is span._skill_parsed_ids

    @pytest.mark.asyncio
    async def test_aexit_does_nothing(self):
        """Test __aexit__ completes without error."""
        span = AgentRunSkillSpan(skill_retriever=None, skill_ids=[])

        # Should not raise any exception
        await span.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_register_skills_async_no_retriever(self):
        """Test register_skills_async returns early when no retriever."""
        mock_tool_span = MagicMock(spec=AgentRunToolSpan)
        mock_tool_register = MagicMock()

        span = AgentRunSkillSpan(skill_retriever=None, skill_ids=["skill1"])

        result = await span.register_skills_async(
            agent_tool_span=mock_tool_span,
            agent_tool_register=mock_tool_register,
        )

        assert result is span
        mock_tool_span.register_tool_async.assert_not_called()
        mock_tool_register.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_skills_async_no_parsed_ids(self):
        """Test register_skills_async returns early when no parsed IDs."""
        mock_retriever = MagicMock(spec=SkillRetriever)
        mock_tool_span = MagicMock(spec=AgentRunToolSpan)
        mock_tool_register = MagicMock()

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=[])
        await span.__aenter__()

        result = await span.register_skills_async(
            agent_tool_span=mock_tool_span,
            agent_tool_register=mock_tool_register,
        )

        assert result is span
        mock_tool_span.register_tool_async.assert_not_called()
        mock_tool_register.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_skills_async_with_callback(self):
        """Test register_skills_async registers skill tool with callback."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        # Create a mock skill tool
        mock_skill_tool = MagicMock(spec=Tool)
        mock_skill_tool.name = "skills"
        mock_retriever.to_tool = MagicMock(return_value=mock_skill_tool)

        # Mock tool span
        mock_tool_span = MagicMock(spec=AgentRunToolSpan)
        mock_tool_span.register_tool_async = AsyncMock(return_value=[mock_skill_tool])

        # Mock tool register callback
        mock_tool_register = MagicMock()

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])

        # Manually set parsed IDs (simulate __aenter__)
        span._skill_parsed_ids = ["skill1"]

        result = await span.register_skills_async(
            agent_tool_span=mock_tool_span,
            agent_tool_register=mock_tool_register,
        )

        assert result is span

        # Should call to_tool with skill_ids and callback
        mock_retriever.to_tool.assert_called_once()
        call_kwargs = mock_retriever.to_tool.call_args[1]
        assert call_kwargs["skill_ids"] == ["skill1"]
        assert callable(call_kwargs["load_callback"])

        # Should register the skill tool
        mock_tool_span.register_tool_async.assert_called_once_with(mock_skill_tool)
        mock_tool_register.assert_called_once_with(mock_skill_tool)

    @pytest.mark.asyncio
    async def test_register_skills_async_callback_registers_tools(self):
        """Test the callback passed to to_tool registers skill's tools."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        # Create a skill config with tool_ids
        test_skill = SkillConfig(
            id="skill1",
            description="Test skill",
            tool_ids=["tool1", "tool2"],
        )

        # Create mock tools
        mock_tool1 = MagicMock(spec=Tool)
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock(spec=Tool)
        mock_tool2.name = "tool2"

        mock_skill_tool = MagicMock(spec=Tool)
        mock_skill_tool.name = "skills"
        mock_retriever.to_tool = MagicMock(return_value=mock_skill_tool)

        # Mock tool span
        mock_tool_span = MagicMock(spec=AgentRunToolSpan)

        # Configure register_tool_async to return different tools based on input
        async def mock_register(tool_id):
            if tool_id == "tool1":
                return [mock_tool1]
            elif tool_id == "tool2":
                return [mock_tool2]
            elif tool_id == mock_skill_tool:
                return [mock_skill_tool]
            return []

        mock_tool_span.register_tool_async = AsyncMock(side_effect=mock_register)

        # Mock tool register callback
        registered_tools = []

        def mock_tool_register(tool):
            registered_tools.append(tool)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])
        span._skill_parsed_ids = ["skill1"]

        await span.register_skills_async(
            agent_tool_span=mock_tool_span,
            agent_tool_register=mock_tool_register,
        )

        # Extract the callback
        call_kwargs = mock_retriever.to_tool.call_args[1]
        callback = call_kwargs["load_callback"]

        # Invoke the callback with the test skill
        await callback(test_skill)

        # The callback should have registered tool1 and tool2
        assert mock_tool1 in registered_tools
        assert mock_tool2 in registered_tools

        # Verify register_tool_async was called for both tools
        assert call("tool1") in mock_tool_span.register_tool_async.call_args_list
        assert call("tool2") in mock_tool_span.register_tool_async.call_args_list

    @pytest.mark.asyncio
    async def test_register_skills_async_callback_handles_empty_tool_ids(self):
        """Test callback handles skill with no tool_ids gracefully."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        # Skill with no tool_ids
        test_skill = SkillConfig(
            id="skill1",
            description="Test skill",
            tool_ids=None,
        )

        mock_skill_tool = MagicMock(spec=Tool)
        mock_retriever.to_tool = MagicMock(return_value=mock_skill_tool)

        mock_tool_span = MagicMock(spec=AgentRunToolSpan)
        mock_tool_span.register_tool_async = AsyncMock(return_value=[mock_skill_tool])

        registered_tools = []

        def mock_tool_register(tool):
            registered_tools.append(tool)

        span = AgentRunSkillSpan(skill_retriever=mock_retriever, skill_ids=["skill1"])
        span._skill_parsed_ids = ["skill1"]

        await span.register_skills_async(
            agent_tool_span=mock_tool_span,
            agent_tool_register=mock_tool_register,
        )

        # Extract and invoke the callback
        call_kwargs = mock_retriever.to_tool.call_args[1]
        callback = call_kwargs["load_callback"]
        await callback(test_skill)

        # Should complete without error, no tools registered via callback
        # (only the skill tool itself should be registered)
        assert mock_skill_tool in registered_tools

    @pytest.mark.asyncio
    async def test_context_manager_full_lifecycle(self):
        """Test full context manager lifecycle."""
        mock_retriever = MagicMock(spec=SkillRetriever)

        skill1 = SkillConfig(
            id="skill1",
            description="Path skill",
            path="/path/to/skill1",
        )
        skill2 = SkillConfig(
            id="skill2",
            description="ID skill",
            tool_ids=["tool1"],
        )

        async def mock_get_skill(sid):
            skills = {"skill1": skill1, "skill2": skill2}
            return skills.get(sid)

        mock_retriever.get_skill_async = mock_get_skill

        # Use as context manager
        async with AgentRunSkillSpan(
            skill_retriever=mock_retriever, skill_ids=["skill1", "skill2"]
        ) as span:
            assert span.get_skill_paths() == ["/path/to/skill1"]
            assert span.get_skill_ids() == ["skill2"]
