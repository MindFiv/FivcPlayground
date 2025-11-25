#!/usr/bin/env python3
"""
Regression tests for TaskGroup error fixes.

These tests prevent regression of the TaskGroup error that occurred when:
1. setup_tools() created nested lists instead of flattening ToolBundle results
2. LangChain backend had syntax errors in function signatures

Issue: https://github.com/MindFiv/FivcAdvisor/issues/XXX
"""

import sys
import pytest
from unittest.mock import Mock
from contextlib import asynccontextmanager

from fivcplayground.tools import setup_tools
from fivcplayground.tools.types.backends import ToolBundle
import fivcplayground


class TestSetupToolsListFlattening:
    """Test that setup_tools() properly flattens ToolBundle results."""

    @pytest.mark.asyncio
    async def test_setup_tools_flattens_tool_bundle_results(self):
        """Test that ToolBundle tools are flattened, not nested."""
        # Create mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool3 = Mock()
        mock_tool3.name = "tool3"

        # Create a mock ToolBundle that returns a list of tools
        mock_bundle = Mock(spec=ToolBundle)

        @asynccontextmanager
        async def mock_load_async():
            yield [mock_tool1, mock_tool2]

        mock_bundle.load_async = mock_load_async

        # Call setup_tools with a mix of regular tools and bundles
        tools_input = [mock_bundle, mock_tool3]

        tools_expanded = []
        async with setup_tools(tools_input) as result:
            tools_expanded = result

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
    async def test_setup_tools_handles_multiple_bundles(self):
        """Test setup_tools with multiple ToolBundles."""
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

        @asynccontextmanager
        async def mock_load_async_1():
            yield [bundle1_tool1, bundle1_tool2]

        @asynccontextmanager
        async def mock_load_async_2():
            yield [bundle2_tool1]

        mock_bundle1.load_async = mock_load_async_1
        mock_bundle2.load_async = mock_load_async_2

        # Call setup_tools with multiple bundles
        tools_input = [mock_bundle1, mock_bundle2]

        async with setup_tools(tools_input) as result:
            tools_expanded = result

        # Verify all tools are flattened
        assert len(tools_expanded) == 3
        assert tools_expanded[0] == bundle1_tool1
        assert tools_expanded[1] == bundle1_tool2
        assert tools_expanded[2] == bundle2_tool1

        # Verify no nested lists
        for tool in tools_expanded:
            assert not isinstance(tool, list)

    @pytest.mark.asyncio
    async def test_setup_tools_with_empty_bundle(self):
        """Test setup_tools handles empty ToolBundle results."""
        mock_tool = Mock()
        mock_tool.name = "regular_tool"

        mock_bundle = Mock(spec=ToolBundle)

        @asynccontextmanager
        async def mock_load_async():
            yield []

        mock_bundle.load_async = mock_load_async

        tools_input = [mock_bundle, mock_tool]

        async with setup_tools(tools_input) as result:
            tools_expanded = result

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
        "fivcplayground.agents.types.backends",
        "fivcplayground.agents.types.backends.langchain",
        "fivcplayground.tools.types.backends",
        "fivcplayground.tools.types.backends.langchain",
        "fivcplayground.models.types.backends",
        "fivcplayground.models.types.backends.langchain",
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
            import fivcplayground.agents.types.backends.langchain as lc_backend

            assert lc_backend is not None
        except SyntaxError as e:
            pytest.fail(f"LangChain backend has syntax error: {e}")

    def test_langchain_agent_runnable_imports(self, langchain_backend):
        """Test that LangChain AgentRunnable can be imported without syntax errors."""
        try:
            from fivcplayground.agents.types.backends.langchain import AgentRunnable

            assert AgentRunnable is not None
        except SyntaxError as e:
            pytest.fail(f"LangChain AgentRunnable has syntax error: {e}")

    def test_langchain_agent_runnable_has_run_method(self, langchain_backend):
        """Test that AgentRunnable.run() method exists and is callable."""
        from fivcplayground.agents.types.backends.langchain import AgentRunnable

        mock_model = Mock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert hasattr(agent, "run")
        assert callable(agent.run)

    def test_langchain_agent_runnable_has_run_async_method(self, langchain_backend):
        """Test that AgentRunnable.run_async() method exists and is callable."""
        from fivcplayground.agents.types.backends.langchain import AgentRunnable

        mock_model = Mock()
        agent = AgentRunnable(model=mock_model, id="test-agent")

        assert hasattr(agent, "run_async")
        assert callable(agent.run_async)

    def test_langchain_agent_runnable_event_callback_signature(self, langchain_backend):
        """Test that event_callback parameter accepts proper lambda signature."""
        from fivcplayground.agents.types.backends.langchain import AgentRunnable

        mock_model = Mock()

        # Test with proper lambda signature (should not raise)
        agent = AgentRunnable(
            model=mock_model,
            id="test-agent",
        )

        assert agent is not None
        assert agent.id == "test-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
