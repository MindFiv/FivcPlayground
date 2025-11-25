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
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            assert retriever.max_num == 10
            assert retriever.min_score == 0.0
            assert isinstance(retriever.tools, dict)
            assert len(retriever.tools) == 0
            assert retriever.collection == mock_db.tools

    def test_str(self, mock_embedding_config_repository):
        """Test string representation."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            assert str(retriever) == "ToolRetriever(num_tools=0)"

    def test_cleanup(self, mock_embedding_config_repository):
        """Test cleanup method."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )
            retriever.tools["tool1"] = Mock()
            retriever.max_num = 5
            retriever.min_score = 0.5

            retriever.cleanup()

            assert retriever.max_num == 10
            assert retriever.min_score == 1.0
            assert len(retriever.tools) == 0
            assert retriever.collection.cleanup.call_count >= 1

    def test_add_tool(self, mock_embedding_config_repository, mock_tool):
        """Test adding a tool."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            retriever.add_tool(mock_tool)

            assert "test_tool" in retriever.tools
            assert retriever.tools["test_tool"] == mock_tool
            retriever.collection.add.assert_called_once()

    def test_add_duplicate_tool(self, mock_embedding_config_repository, mock_tool):
        """Test that adding duplicate tool raises ValueError."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )
            retriever.add_tool(mock_tool)

            with pytest.raises(ValueError, match="Duplicate tool name"):
                retriever.add_tool(mock_tool)

    def test_add_tool_without_description(self, mock_embedding_config_repository):
        """Test that adding tool without description raises ValueError."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )
            tool = create_mock_tool("bad_tool", "")

            with pytest.raises(ValueError, match="Tool description is empty"):
                retriever.add_tool(tool)

    def test_get_tool(self, mock_embedding_config_repository, mock_tool):
        """Test getting a tool by name."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )
            retriever.add_tool(mock_tool)

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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            tool1 = create_mock_tool("tool1", "Tool 1")
            tool2 = create_mock_tool("tool2", "Tool 2")

            retriever.add_tool(tool1)
            retriever.add_tool(tool2)

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
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
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
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            retriever.add_tool(tool1)
            retriever.add_tool(tool2)

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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )
            retriever.retrieve_min_score = 0.8

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            retriever.add_tool(tool1)
            retriever.add_tool(tool2)

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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            tool1 = create_mock_tool("calculator", "Calculate math")

            retriever.add_tool(tool1)

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
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
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

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            # Create mock tools
            tool1 = create_mock_tool("tool1", "Tool 1")
            tool2 = create_mock_tool("tool2", "Tool 2")

            # Add tools to retriever
            retriever.add_tool(tool1)
            retriever.add_tool(tool2)

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

    def test_remove_tool(self, mock_embedding_config_repository):
        """Test removing a tool."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.count = Mock(return_value=0)
            mock_chroma_collection = Mock()
            mock_chroma_collection.get = Mock(
                return_value={
                    "ids": ["id1", "id2"],
                    "metadatas": [
                        {"__tool__": "test_tool"},
                        {"__tool__": "test_tool"},
                    ],
                }
            )
            mock_chroma_collection.delete = Mock()
            mock_embedding_table.collection = mock_chroma_collection

            # Mock the delete method to call the chroma collection's delete
            def mock_delete(metadata):
                where_clauses = [
                    {key: {"$eq": value}} for key, value in metadata.items()
                ]
                if len(where_clauses) == 1:
                    where = where_clauses[0]
                else:
                    where = {"$and": where_clauses}
                mock_chroma_collection.delete(where=where)

            mock_embedding_table.delete = mock_delete
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            tool = create_mock_tool("test_tool", "A test tool")
            retriever.add_tool(tool)

            retriever.delete_tool("test_tool")

            assert "test_tool" not in retriever.tools
            # Verify delete was called on the collection with the correct where clause
            mock_chroma_collection.delete.assert_called_once()
            call_kwargs = mock_chroma_collection.delete.call_args[1]
            assert "where" in call_kwargs
            assert call_kwargs["where"] == {"__tool__": {"$eq": "test_tool"}}

    def test_remove_nonexistent_tool(self, mock_embedding_config_repository):
        """Test removing a nonexistent tool raises ValueError."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            with pytest.raises(ValueError, match="Tool not found"):
                retriever.delete_tool("nonexistent")

    def test_remove_tool_with_no_embedding_docs(self, mock_embedding_config_repository):
        """Test removing a tool that has no embedding documents."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_chroma_collection = Mock()
            mock_chroma_collection.get = Mock(
                return_value={
                    "ids": ["id1"],
                    "metadatas": [{"__tool__": "other_tool"}],
                }
            )
            mock_chroma_collection.delete = Mock()
            mock_embedding_table.collection = mock_chroma_collection
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
            )

            tool = create_mock_tool("test_tool", "A test tool")

            retriever.add_tool(tool)

            retriever.delete_tool("test_tool")

            assert "test_tool" not in retriever.tools
            # delete should not be called if no matching docs
            mock_chroma_collection.delete.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
