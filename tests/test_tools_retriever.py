#!/usr/bin/env python3
"""
Tests for the tools retriever module.
"""

import pytest
from unittest.mock import Mock, patch

from fivcplayground import __backend__
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.embeddings.types.base import EmbeddingConfig


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


class TestToolRetriever:
    """Test the ToolRetriever class."""

    @pytest.fixture
    def mock_embedding_config_repository(self):
        """Create a mock embedding config repository."""
        mock_repo = Mock()
        # Return a default embedding config
        mock_repo.get_embedding_config.return_value = EmbeddingConfig(
            id="default",
            provider="openai",
            model="text-embedding-ada-002",
            api_key="sk-test-key",
            base_url="https://api.openai.com/v1",
            dimension=1536,
        )
        return mock_repo

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        return create_mock_tool("test_tool", "A test tool")

    def test_init(self, mock_embedding_config_repository):
        """Test ToolRetriever initialization."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            # Mock the embedding database
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.max_num == 10
            assert retriever.min_score == 0.0
            assert isinstance(retriever.tools, dict)
            assert len(retriever.tools) == 0
            assert retriever.tool_indices == mock_db.tools

    def test_str(self, mock_embedding_config_repository):
        """Test string representation."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert str(retriever) == "ToolRetriever(num_tools=0)"

    def test_index_tools(self, mock_embedding_config_repository):
        """Test indexing tools in the retriever."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("tool1", "Tool 1 description")
            tool2 = create_mock_tool("tool2", "Tool 2 description")

            # Mock the repository to return empty list of tool configs
            mock_embedding_config_repository.list_tool_configs.return_value = []

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_list=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Index the tools
            retriever.index_tools()

            # Verify cleanup was called
            mock_embedding_table.cleanup.assert_called_once()
            # Verify add was called for each tool
            assert mock_embedding_table.add.call_count == 2

    def test_get_tool(self, mock_embedding_config_repository, mock_tool):
        """Test getting a tool by name."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Pass tool during initialization
            retriever = ToolRetriever(
                tool_list=[mock_tool],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            result = retriever.get_tool("test_tool")

            assert result == mock_tool

    def test_get_nonexistent_tool(self, mock_embedding_config_repository):
        """Test getting a nonexistent tool returns None."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Mock the repository to return None for nonexistent tools
            mock_embedding_config_repository.get_tool_config.return_value = None

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            result = retriever.get_tool("nonexistent")

            assert result is None

    def test_list_tools(self, mock_embedding_config_repository):
        """Test listing all tools."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("tool1", "Tool 1")
            tool2 = create_mock_tool("tool2", "Tool 2")

            # Mock the repository to return empty list of tool configs
            mock_embedding_config_repository.list_tool_configs.return_value = []

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_list=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = retriever.list_tools()

            assert len(results) == 2
            assert tool1 in results
            assert tool2 in results

    def test_retrieve_min_score_property(self, mock_embedding_config_repository):
        """Test retrieve_min_score property."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.retrieve_min_score == 0.0

            retriever.retrieve_min_score = 0.5

            assert retriever.retrieve_min_score == 0.5
            assert retriever.min_score == 0.5

    def test_retrieve_max_num_property(self, mock_embedding_config_repository):
        """Test retrieve_max_num property."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.retrieve_max_num == 10

            retriever.retrieve_max_num = 20

            assert retriever.retrieve_max_num == 20
            assert retriever.max_num == 20

    def test_retrieve_tools(self, mock_embedding_config_repository):
        """Test retrieving tools by query."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 0.9,
                    },
                    {
                        "text": "Search the web",
                        "metadata": {"__tool__": "search"},
                        "score": 0.7,
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_list=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = retriever.retrieve_tools("math calculation")

            assert len(results) == 2
            assert tool1 in results
            assert tool2 in results

    def test_retrieve_tools_with_min_score(self, mock_embedding_config_repository):
        """Test retrieving tools with minimum score filter."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 0.9,
                    },
                    {
                        "text": "Search the web",
                        "metadata": {"__tool__": "search"},
                        "score": 0.7,
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_list=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )
            retriever.retrieve_min_score = 0.8

            results = retriever.retrieve_tools("math calculation")

            # Only calculator should be returned (score >= 0.8)
            assert len(results) == 1
            assert tool1 in results
            assert tool2 not in results

    def test_call(self, mock_embedding_config_repository):
        """Test calling retriever as a function."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 0.9,
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")

            # Pass tool during initialization
            retriever = ToolRetriever(
                tool_list=[tool1],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = retriever("math calculation")

            assert len(results) == 1
            assert results[0]["name"] == "calculator"
            assert results[0]["description"] == "Calculate math"

    def test_to_tool(self, mock_embedding_config_repository):
        """Test converting retriever to a tool."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            tool = retriever.to_tool()

            assert tool is not None
            # Check for tool_name (Strands) or name (LangChain)
            assert hasattr(tool, "tool_name") or hasattr(tool, "name")
            # Check for invoke method (both frameworks should have this)
            assert hasattr(tool, "invoke") or callable(tool)

    def test_to_tool_invoke_no_recursion_error(self, mock_embedding_config_repository):
        """Test that to_tool() result can be invoked without recursion error.

        Regression test for issue where str(self.retrieve(query)) caused infinite
        recursion when ToolBundle objects were in the results due to circular
        references in Pydantic models.
        """
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Tool 1",
                        "metadata": {"__tool__": "tool1"},
                        "score": 0.9,
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create mock tools
            tool1 = create_mock_tool("tool1", "Tool 1")
            tool2 = create_mock_tool("tool2", "Tool 2")

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_list=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Convert to tool
            tool = retriever.to_tool()

            # Invoke the tool - this should NOT raise RecursionError
            # Use invoke if available, otherwise call directly
            if hasattr(tool, "invoke"):
                result = tool.invoke({"query": "test query"})
            else:
                result = tool({"query": "test query"})

            # Result should be a string representation of tool metadata
            assert isinstance(result, str)
            assert "tool1" in result


if __name__ == "__main__":
    pytest.main([__file__])
