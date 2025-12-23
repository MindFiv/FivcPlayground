import sys
import pytest
from unittest.mock import Mock, AsyncMock

from fivcplayground.tools import ToolBundle
from fivcplayground.agents import AgentRunToolSpan
import fivcplayground


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

        # Create AgentRunToolSpan with a mix of regular tools and bundles
        span = AgentRunToolSpan()
        span._tools = [mock_bundle, mock_tool3]

        tools_expanded = await span.__aenter__()

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

        # Create AgentRunToolSpan with multiple bundles
        span = AgentRunToolSpan()
        span._tools = [mock_bundle1, mock_bundle2]

        tools_expanded = await span.__aenter__()

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

        # Create AgentRunToolSpan with bundle and regular tool
        span = AgentRunToolSpan()
        span._tools = [mock_bundle, mock_tool]

        tools_expanded = await span.__aenter__()

        # Should have only the regular tool
        assert len(tools_expanded) == 1
        assert tools_expanded[0] == mock_tool


@pytest.fixture
def langchain_backend():
    """
    Fixture that temporarily switches to LangChain backend for testing.

    This fixture:
    1. Saves the original backend value
    2. Monkey-patches fivcplayground.__backend__ to 'langchain'
    3. Clears module caches to force reimport with new backend
    4. Yields control to the test
    5. Restores the original backend and clears caches again

    This ensures LangChain-specific tests actually run with the LangChain backend
    active, not just importing the module while Strands is the active backend.
    """
    original_backend = fivcplayground.__backend__

    # List of modules that need to be reloaded when backend changes
    modules_to_reload = [
        "fivcplayground.backends.langchain.agents",
        "fivcplayground.backends.langchain.models",
        "fivcplayground.backends.strands.agents",
        "fivcplayground.backends.strands.models",
    ]

    # Save original modules
    saved_modules = {name: sys.modules.get(name) for name in modules_to_reload}

    try:
        # Switch to LangChain backend
        fivcplayground.__backend__ = "langchain"

        # Remove modules from cache to force reimport with new backend
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                del sys.modules[module_name]

        yield

    finally:
        # Restore original backend
        fivcplayground.__backend__ = original_backend

        # Restore original modules
        for module_name, module in saved_modules.items():
            if module is None:
                # Module wasn't loaded before, remove it
                if module_name in sys.modules:
                    del sys.modules[module_name]
            else:
                # Restore the original module
                sys.modules[module_name] = module


class TestLangChainBackendSyntax:
    """Test that LangChain backend has correct syntax and works correctly.

    These tests use the langchain_backend fixture to ensure they run with
    the LangChain backend active, not just importing the module.
    """

    def test_langchain_backend_module_imports(self, langchain_backend):
        """Test that LangChain backend module can be imported without syntax errors."""
        try:
            import fivcplayground.backends.langchain.agents as lc_backend

            assert lc_backend is not None
        except SyntaxError as e:
            pytest.fail(f"LangChain backend has syntax error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
