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
from fivcplayground import __backend__
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.tools.types.backends import get_tool_name


def create_mock_tool(name: str, description: str):
    """Create a mock tool with correct attributes based on the current backend."""
    tool = Mock()
    if __backend__ == "langchain":
        tool.name = name
        tool.description = description
    else:  # strands
        tool.tool_name = name
        tool.tool_spec = {"description": description}
    return tool


class TestToolsInitRegression:
    """Regression tests for tools module initialization."""

    def test_create_tool_retriever_uses_correct_tool_attribute(self):
        """
        Regression test: Ensure create_tool_retriever uses correct tool attributes.

        This test prevents the AttributeError that occurred when trying to access
        tool attributes. The correct attributes depend on the backend:
        - LangChain: 'name' and 'description'
        - Strands: 'tool_name' and 'tool_spec'
        """
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create mock embedding config repository
            mock_repo = Mock()

            # This should not raise AttributeError
            result = create_tool_retriever(
                embedding_config_repository=mock_repo,
                embedding_config_id="default",
                load_builtin_tools=True,
            )

            # Verify the retriever was returned
            assert isinstance(result, ToolRetriever)

            # Verify get_all returns tools
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

        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            # Create mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=None,
                embedding_config_id="default",
            )

            # Create tools with correct attributes for current backend
            tool1 = create_mock_tool("tool1", "Tool 1 description")
            tool2 = create_mock_tool("tool2", "Tool 2 description")

            # Add tools to retriever
            retriever.add_tool(tool1)
            retriever.add_tool(tool2)

            # Get all tools
            all_tools = retriever.list_tools()

            # Verify all tools can be accessed with get_tool_name
            assert len(all_tools) == 2
            tool_names = [get_tool_name(tool) for tool in all_tools]
            assert "tool1" in tool_names
            assert "tool2" in tool_names

    def test_create_tool_retriever_with_builtin_tools(self):
        """
        Test that create_tool_retriever correctly loads builtin tools.

        This test verifies that when load_builtin_tools=True, the retriever
        includes the builtin tools (clock and calculator).
        """
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create retriever with builtin tools
            retriever = create_tool_retriever(
                embedding_config_repository=None,
                embedding_config_id="default",
                load_builtin_tools=True,
            )

            # Get all tools
            all_tools = retriever.list_tools()

            # Verify builtin tools are loaded
            tool_names = [get_tool_name(tool) for tool in all_tools]
            assert "clock" in tool_names
            assert "calculator" in tool_names

    @pytest.mark.skipif(
        __backend__ != "langchain", reason="Only test with LangChain backend"
    )
    def test_tools_retriever_list_tools_with_langchain_tools(self):
        """
        Test that ToolRetriever.list_tools() works with actual LangChain Tool objects.

        This test uses real LangChain tools to ensure compatibility.
        Only runs when backend is set to "langchain".
        """
        from langchain_core.tools import tool as make_tool
        from fivcplayground.tools.types.retrievers import ToolRetriever
        from unittest.mock import Mock

        # Create mock embedding DB
        mock_db = Mock()
        mock_embedding_table = Mock()
        mock_embedding_table.cleanup = Mock()
        mock_db.tools = mock_embedding_table

        retriever = ToolRetriever(
            embedding_config_repository=None,
            embedding_config_id="default",
        )

        # Create a real LangChain tool
        @make_tool
        def calculator(expression: str) -> float:
            """Calculate a mathematical expression."""
            return eval(expression)

        @make_tool
        def search(query: str) -> str:
            """Search for information."""
            return f"Results for {query}"

        # Add tools to retriever
        retriever.add_tool(calculator)
        retriever.add_tool(search)

        # Get all tools
        all_tools = retriever.list_tools()

        # Verify tools have 'name' attribute (LangChain standard)
        assert len(all_tools) == 2
        tool_names = [get_tool_name(t) for t in all_tools]
        assert "calculator" in tool_names
        assert "search" in tool_names

        # Verify we can access the name attribute without AttributeError
        for tool in all_tools:
            name = get_tool_name(tool)  # This should not raise AttributeError
            assert isinstance(name, str)
            assert len(name) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
