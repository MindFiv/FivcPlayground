#!/usr/bin/env python3
"""
Regression tests for tools module initialization.

This module contains tests to prevent regressions in the tools initialization
process, particularly around tool attribute access.

Regression: https://github.com/FivcPlayground/fivcadvisor/issues/XXX
- Issue: AttributeError: 'StructuredTool' object has no attribute 'tool_name'
- Root Cause: Code was accessing tool.tool_name instead of tool.name
- Fix: Changed to use tool.name which is the correct LangChain Tool attribute
"""

import pytest
from unittest.mock import Mock, patch
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.backends.langchain.tools import LangchainToolBackend
from fivcplayground.backends.strands.tools import StrandsToolBackend

# Test with both backends
get_tool_backends = [
    ("langchain", lambda: LangchainToolBackend()),
    ("strands", lambda: StrandsToolBackend()),
]


def create_mock_tool(name: str, description: str):
    """Create a mock tool with correct attributes based on the current backend."""

    # Create a simple object with the required attributes
    # Set both name/description (Tool interface) and tool_name/tool_spec (backend-specific)
    class SimpleTool:
        pass

    tool = SimpleTool()
    # Set attributes for both backends to ensure compatibility
    tool.name = name
    tool.description = description
    tool.tool_name = name
    tool.tool_spec = {"description": description}
    return tool


class TestToolsInitRegression:
    """Regression tests for tools module initialization."""

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_create_tool_retriever_uses_correct_tool_attribute(
        self, backend_name, get_backend
    ):
        """
        Regression test: Ensure create_tool_retriever uses correct tool attributes.

        This test prevents the AttributeError that occurred when trying to access
        tool attributes. The correct attributes depend on the backend:
        - LangChain: 'name' and 'description'
        - Strands: 'tool_name' and 'tool_spec'
        """
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # This should not raise AttributeError
            result = create_tool_retriever(
                tool_backend=get_backend(),
                load_builtin_tools=True,
            )

            # Verify the retriever was returned
            assert isinstance(result, ToolRetriever)

            # Verify list_tools returns tools
            all_tools = result.list_tools()
            assert len(all_tools) >= 0  # May have builtin tools

    def test_list_tools_returns_tools_with_name_attribute(self):
        """
        Test that ToolRetriever.list_tools() returns tools with correct attributes.

        This ensures that tools returned from list_tools() have the correct
        attributes for the current backend (name for LangChain, tool_name for Strands).
        """
        from fivcplayground.tools.types.retrievers import ToolRetriever
        from unittest.mock import Mock

        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            # Create mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create tools with correct attributes for current backend
            tool1 = create_mock_tool("tool1", "Tool 1 description")
            tool2 = create_mock_tool("tool2", "Tool 2 description")

            # Mock the tool config repository to return no tool configs
            # This ensures list_tools() only returns the tools we explicitly added
            with patch(
                "fivcplayground.tools.types.repositories.files.FileToolConfigRepository"
            ) as mock_repo_class:
                mock_repo = Mock()
                mock_repo.list_tool_configs.return_value = []
                mock_repo_class.return_value = mock_repo

                retriever = ToolRetriever(
                    tool_backend=LangchainToolBackend(),  # Use LangChain for this test
                    tool_list=[tool1, tool2],
                    embedding_db=mock_db,
                    tool_config_repository=mock_repo,
                )

                # Get all tools
                all_tools = retriever.list_tools()

                # Verify all tools can be accessed with .name property
                assert len(all_tools) == 2
                tool_names = [tool.name for tool in all_tools]
                assert "tool1" in tool_names
                assert "tool2" in tool_names

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_create_tool_retriever_with_builtin_tools(self, backend_name, get_backend):
        """
        Test that create_tool_retriever correctly loads builtin tools.

        This test verifies that when load_builtin_tools=True, the retriever
        includes the builtin tools (clock and calculator).
        """
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create retriever with builtin tools
            retriever = create_tool_retriever(
                tool_backend=get_backend(),
                load_builtin_tools=True,
            )

            # Get all tools
            all_tools = retriever.list_tools()

            # Verify builtin tools are loaded
            tool_names = [tool.name for tool in all_tools]
            assert "clock" in tool_names
            assert "calculator" in tool_names

    def test_tools_retriever_list_tools_with_langchain_tools(self):
        """
        Test that ToolRetriever.list_tools() works with LangChain backend.

        This test verifies that tools wrapped by LangChain backend have correct attributes.
        """
        from fivcplayground.tools.types.retrievers import ToolRetriever
        from unittest.mock import Mock

        # Create mock embedding DB
        mock_db = Mock()
        mock_embedding_table = Mock()
        mock_embedding_table.cleanup = Mock()
        mock_db.tools = mock_embedding_table

        # Create mock tool config repository
        mock_repo = Mock()
        mock_repo.list_tool_configs.return_value = []

        # Create simple Python functions to wrap
        def calculator(expression: str) -> float:
            """Calculate a mathematical expression."""
            return eval(expression)

        def search(query: str) -> str:
            """Search for information."""
            return f"Results for {query}"

        # Wrap tools with the backend
        backend = LangchainToolBackend()
        wrapped_calculator = backend.create_tool(calculator)
        wrapped_search = backend.create_tool(search)

        # Create a retriever with the tools
        retriever_with_tools = ToolRetriever(
            tool_backend=backend,
            tool_list=[wrapped_calculator, wrapped_search],
            embedding_db=mock_db,
            tool_config_repository=mock_repo,
        )

        # Get all tools
        all_tools = retriever_with_tools.list_tools()

        # Verify tools have 'name' attribute (Tool interface standard)
        assert len(all_tools) == 2
        tool_names = [t.name for t in all_tools]
        assert "calculator" in tool_names
        assert "search" in tool_names

        # Verify we can access the name attribute without AttributeError
        for tool in all_tools:
            name = tool.name  # This should not raise AttributeError
            assert isinstance(name, str)
            assert len(name) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
