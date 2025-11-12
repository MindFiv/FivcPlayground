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
from unittest.mock import Mock, patch, MagicMock
from fivcplayground import __backend__
from fivcplayground.tools import _load_retriever
from fivcplayground.tools.types.retrievers import ToolsRetriever
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

    def test_load_retriever_uses_correct_tool_attribute(self):
        """
        Regression test: Ensure _load_retriever uses correct tool attributes.

        This test prevents the AttributeError that occurred when trying to access
        tool attributes. The correct attributes depend on the backend:
        - LangChain: 'name' and 'description'
        - Strands: 'tool_name' and 'tool_spec'
        """
        with patch("fivcplayground.tools.ToolsLoader") as mock_loader_class:
            with patch("fivcplayground.tools.ToolsRetriever") as mock_retriever_class:
                # Setup mock retriever
                mock_retriever = MagicMock(spec=ToolsRetriever)

                # Create mock tools with correct attributes for current backend
                mock_tool1 = create_mock_tool(
                    "calculator", "Calculate math expressions"
                )
                mock_tool2 = create_mock_tool("search", "Search the web")

                # Setup get_all to return tools
                mock_retriever.get_all.return_value = [mock_tool1, mock_tool2]

                mock_retriever_class.return_value = mock_retriever
                mock_loader_class.return_value = Mock()

                # This should not raise AttributeError
                result = _load_retriever()

                # Verify the retriever was returned
                assert result == mock_retriever

                # Verify get_all was called
                mock_retriever.get_all.assert_called()

    def test_get_all_returns_tools_with_name_attribute(self):
        """
        Test that ToolsRetriever.get_all() returns tools with correct attributes.

        This ensures that tools returned from get_all() have the correct
        attributes for the current backend (name for LangChain, tool_name for Strands).
        """
        from fivcplayground.tools.types.retrievers import ToolsRetriever
        from unittest.mock import Mock

        # Create mock embedding DB
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection

        retriever = ToolsRetriever(db=mock_db)

        # Create tools with correct attributes for current backend
        tool1 = create_mock_tool("tool1", "Tool 1 description")
        tool2 = create_mock_tool("tool2", "Tool 2 description")

        # Add tools to retriever
        retriever.add(tool1)
        retriever.add(tool2)

        # Get all tools
        all_tools = retriever.get_all()

        # Verify all tools can be accessed with get_tool_name
        assert len(all_tools) == 2
        tool_names = [get_tool_name(tool) for tool in all_tools]
        assert "tool1" in tool_names
        assert "tool2" in tool_names

    def test_print_statement_uses_tool_name_attribute(self, capsys):
        """
        Test that the print statement in _load_retriever uses correct tool names.

        This test captures the print output and verifies that tool names are
        correctly extracted using the backend-agnostic get_tool_name function.
        """
        with patch("fivcplayground.tools.ToolsLoader") as mock_loader_class:
            with patch("fivcplayground.tools.ToolsRetriever") as mock_retriever_class:
                # Setup mock retriever
                mock_retriever = MagicMock(spec=ToolsRetriever)

                # Create mock tools with correct attributes for current backend
                mock_tool1 = create_mock_tool("calculator", "Calculate math")
                mock_tool2 = create_mock_tool("search", "Search the web")

                mock_retriever.get_all.return_value = [mock_tool1, mock_tool2]
                mock_retriever_class.return_value = mock_retriever
                mock_loader_class.return_value = Mock()

                # Call _load_retriever
                _load_retriever()

                # Capture printed output
                captured = capsys.readouterr()

                # Verify the print statement contains tool names
                assert "Registered Tools:" in captured.out
                assert "calculator" in captured.out
                assert "search" in captured.out

    @pytest.mark.skipif(
        __backend__ != "langchain", reason="Only test with LangChain backend"
    )
    def test_tools_retriever_get_all_with_langchain_tools(self):
        """
        Test that ToolsRetriever.get_all() works with actual LangChain Tool objects.

        This test uses real LangChain tools to ensure compatibility.
        Only runs when backend is set to "langchain".
        """
        from langchain_core.tools import tool as make_tool
        from fivcplayground.tools.types.retrievers import ToolsRetriever
        from unittest.mock import Mock

        # Create mock embedding DB
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection

        retriever = ToolsRetriever(db=mock_db)

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
        retriever.add(calculator)
        retriever.add(search)

        # Get all tools
        all_tools = retriever.get_all()

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
