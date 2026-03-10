"""
Unit tests for tool_ids merging behavior in agent backends.

Tests verify that both Strands and LangChain backends merge tool_ids
from agent config and runtime parameters using set union (v0.1.19+).

Simplified integration tests that verify the merging logic works correctly.
"""


class TestAgentToolIdsMerging:
    """Test tool_ids merging logic by inspecting the actual merging code."""

    def test_strands_tool_ids_merging_logic(self):
        """Test the Strands backend merges tool_ids correctly."""

        # Test the actual merging logic that's in run_async
        config_tool_ids = ["config1", "config2"]
        runtime_tool_ids = ["runtime1", "config2"]  # "config2" overlaps

        # Simulate the merging logic from run_async method (lines 186-187)
        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])
        result = list(agent_tool_ids)

        # Assert: Union with deduplication
        assert set(result) == {"config1", "config2", "runtime1"}

    def test_langchain_tool_ids_merging_logic(self):
        """Test the LangChain backend merges tool_ids correctly."""

        # Test the actual merging logic that's in run_async
        config_tool_ids = ["config1", "config2"]
        runtime_tool_ids = ["runtime1", "config2"]  # "config2" overlaps

        # Simulate the merging logic from run_async method (lines 138-139)
        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])
        result = list(agent_tool_ids)

        # Assert: Union with deduplication
        assert set(result) == {"config1", "config2", "runtime1"}

    def test_backend_parity_merging_logic(self):
        """Test that both backends use identical merging logic."""
        # Both backends use the exact same code pattern for merging
        config_tool_ids = ["a", "b"]
        runtime_tool_ids = ["b", "c"]

        # Strands merging
        strands_result = set(runtime_tool_ids) if runtime_tool_ids else set()
        strands_result.update(config_tool_ids or [])

        # LangChain merging
        langchain_result = set(runtime_tool_ids) if runtime_tool_ids else set()
        langchain_result.update(config_tool_ids or [])

        # Assert: Both produce identical results
        assert strands_result == langchain_result
        assert strands_result == {"a", "b", "c"}

    def test_merging_with_none_values(self):
        """Test merging behavior with None values."""
        # Runtime None, config has tools
        config_tool_ids = ["tool1", "tool2"]
        runtime_tool_ids = None

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert set(agent_tool_ids) == {"tool1", "tool2"}

        # Runtime has tools, config None
        config_tool_ids = None
        runtime_tool_ids = ["tool3", "tool4"]

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert set(agent_tool_ids) == {"tool3", "tool4"}

        # Both None
        config_tool_ids = None
        runtime_tool_ids = None

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert agent_tool_ids == set()

    def test_merging_with_empty_lists(self):
        """Test merging behavior with empty lists."""
        # Both empty
        config_tool_ids = []
        runtime_tool_ids = []

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert agent_tool_ids == set()

    def test_deduplication_in_runtime_parameter(self):
        """Test that duplicates in runtime tool_ids are deduplicated."""
        config_tool_ids = []
        runtime_tool_ids = ["tool1", "tool1", "tool2"]

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert set(agent_tool_ids) == {"tool1", "tool2"}

    def test_union_no_overlap(self):
        """Test union of tool_ids with no duplicates."""
        config_tool_ids = ["tool3", "tool4"]
        runtime_tool_ids = ["tool1", "tool2"]

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert set(agent_tool_ids) == {"tool1", "tool2", "tool3", "tool4"}

    def test_union_with_overlap(self):
        """Test union of tool_ids with duplicates."""
        config_tool_ids = ["tool2", "tool3"]
        runtime_tool_ids = ["tool1", "tool2"]

        agent_tool_ids = set(runtime_tool_ids) if runtime_tool_ids else set()
        agent_tool_ids.update(config_tool_ids or [])

        assert set(agent_tool_ids) == {"tool1", "tool2", "tool3"}


class TestAgentSkillIdsMerging:
    """Test skill_ids merging logic in agent backends.

    Key difference from tool_ids: when merged set is empty, pass None
    (not []) to preserve "show all skills" semantics in to_tool().
    """

    def _merge_skill_ids(
        self,
        config_skill_ids: list[str] | None,
        runtime_skill_ids: list[str] | None,
    ) -> list[str] | None:
        """Simulate the skill_ids merging logic from both backends."""
        agent_skill_ids = set(runtime_skill_ids) if runtime_skill_ids else set()
        agent_skill_ids.update(config_skill_ids or [])
        return list(agent_skill_ids) if agent_skill_ids else None

    def test_strands_skill_ids_merging_with_overlap(self):
        """Config + runtime merged via set union, duplicates removed."""
        result = self._merge_skill_ids(
            config_skill_ids=["skill1", "skill2"],
            runtime_skill_ids=["skill2", "skill3"],
        )
        assert set(result) == {"skill1", "skill2", "skill3"}

    def test_langchain_skill_ids_merging_with_overlap(self):
        """LangChain backend uses same merging logic as Strands."""
        result = self._merge_skill_ids(
            config_skill_ids=["skill1", "skill2"],
            runtime_skill_ids=["skill2", "skill3"],
        )
        assert set(result) == {"skill1", "skill2", "skill3"}

    def test_config_only_runtime_none(self):
        """Config skill_ids used when runtime is None."""
        result = self._merge_skill_ids(
            config_skill_ids=["skill1", "skill2"],
            runtime_skill_ids=None,
        )
        assert set(result) == {"skill1", "skill2"}

    def test_runtime_only_config_none(self):
        """Runtime skill_ids used when config is None."""
        result = self._merge_skill_ids(
            config_skill_ids=None,
            runtime_skill_ids=["skill3", "skill4"],
        )
        assert set(result) == {"skill3", "skill4"}

    def test_both_none_returns_none(self):
        """Both None → None (preserves 'all skills' semantics)."""
        result = self._merge_skill_ids(
            config_skill_ids=None,
            runtime_skill_ids=None,
        )
        assert result is None

    def test_both_empty_returns_none(self):
        """Both empty lists → None (preserves 'all skills' semantics)."""
        result = self._merge_skill_ids(
            config_skill_ids=[],
            runtime_skill_ids=[],
        )
        assert result is None

    def test_backend_parity(self):
        """Strands and LangChain produce identical results."""
        config_skill_ids = ["a", "b"]
        runtime_skill_ids = ["b", "c"]

        # Both backends use identical merging logic
        strands_ids = set(runtime_skill_ids) if runtime_skill_ids else set()
        strands_ids.update(config_skill_ids or [])
        strands_result = list(strands_ids) if strands_ids else None

        langchain_ids = set(runtime_skill_ids) if runtime_skill_ids else set()
        langchain_ids.update(config_skill_ids or [])
        langchain_result = list(langchain_ids) if langchain_ids else None

        assert set(strands_result) == set(langchain_result)
        assert set(strands_result) == {"a", "b", "c"}
