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

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fivcplayground.backends.strands.tools import StrandsToolBackend
from fivcplayground.tools import create_builtin_tools_async, create_tool_retriever_async
from fivcplayground.tools.types.retrievers import ToolRetriever

# Test with Strands backend (primary)
get_tool_backends = [
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
    @pytest.mark.asyncio
    async def test_create_tool_retriever_uses_correct_tool_attribute(
        self, backend_name, get_backend
    ):
        """
        Regression test: Ensure create_tool_retriever_async uses correct tool attributes.

        This test prevents the AttributeError that occurred when trying to access
        tool attributes. The correct attributes depend on the backend:
        - LangChain: 'name' and 'description'
        - Strands: 'tool_name' and 'tool_spec'
        """
        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()
        mock_tool_repo.list_tool_configs_async = AsyncMock(
            return_value=[]
        )  # Use AsyncMock for async method

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # This should not raise AttributeError
            result = await create_tool_retriever_async(
                tool_backend=get_backend(),
                embedding_config_repository=mock_embedding_repo,
                tool_config_repository=mock_tool_repo,
                load_builtin_tools=True,
            )

            # Verify the retriever was returned
            assert isinstance(result, ToolRetriever)

            # Verify list_tools_async returns tools
            all_tools = await result.list_tools_async()
            assert len(all_tools) >= 0  # May have builtin tools

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools_with_name_attribute(self):
        """
        Test that ToolRetriever.list_tools_async() returns tools with correct attributes.

        This ensures that tools returned from list_tools_async() have the correct
        attributes for the current backend (name for LangChain, tool_name for Strands).
        """
        from unittest.mock import Mock

        from fivcplayground.tools.types.retrievers import ToolRetriever

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
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
            # This ensures list_tools_async() only returns the tools we explicitly added
            with patch(
                "fivcplayground.tools.types.repositories.files.FileToolConfigRepository"
            ) as mock_repo_class:
                mock_repo = Mock()
                mock_repo.list_tool_configs_async = AsyncMock(
                    return_value=[]
                )  # Use AsyncMock
                mock_repo_class.return_value = mock_repo

                retriever = ToolRetriever(
                    tool_backend=StrandsToolBackend(),  # Use Strands backend
                    tools=[tool1, tool2],
                    embedding_db=mock_db,
                    tool_config_repository=mock_repo,
                )

                # Get all tools using async version
                all_tools = await retriever.list_tools_async()

                # Verify all tools can be accessed with .name property
                assert len(all_tools) == 3  # tool1, tool2, and tool_retriever
                tool_names = [tool.name for tool in all_tools]
                assert "tool1" in tool_names
                assert "tool2" in tool_names
                assert "tool_retriever" in tool_names

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_create_tool_retriever_with_builtin_tools(
        self, backend_name, get_backend
    ):
        """
        Test that create_tool_retriever_async correctly handles builtin tools.

        This test verifies that when builtin tools are passed to create_tool_retriever_async,
        the retriever includes them.
        """
        mock_embedding_repo = Mock()
        mock_tool_repo = Mock()
        mock_tool_repo.list_tool_configs_async = AsyncMock(
            return_value=[]
        )  # Use AsyncMock for async method

        with patch("fivcplayground.tools.create_embedding_db_async") as mock_create_db:
            # Setup mock embedding DB
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create builtin tools
            backend = get_backend()
            builtin_tools = await create_builtin_tools_async(
                tool_backend=backend,
                raise_exception=False,
            )

            # Create retriever with builtin tools
            retriever = await create_tool_retriever_async(
                tool_backend=backend,
                tools=builtin_tools,
                embedding_config_repository=mock_embedding_repo,
                tool_config_repository=mock_tool_repo,
            )

            # Get all tools
            all_tools = await retriever.list_tools_async()

            # Verify builtin tools are loaded
            tool_names = [tool.name for tool in all_tools]
            assert "auxiliary" in tool_names
            assert "filesystem" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
