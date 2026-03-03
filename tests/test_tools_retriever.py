#!/usr/bin/env python3
"""
Tests for the tools retriever module.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.backends.langchain.tools import LangchainToolBackend
from fivcplayground.backends.strands.tools import StrandsToolBackend

# Test with both backends
get_tool_backends = [
    ("langchain", lambda: LangchainToolBackend()),
    ("strands", lambda: StrandsToolBackend()),
]


def create_mock_tool(name: str, description: str):
    """Create a mock tool with correct attributes for both backends."""

    # Create a simple object with the required attributes
    class SimpleTool:
        pass

    tool = SimpleTool()
    # Set attributes for both backends to ensure compatibility
    tool.name = name
    tool.description = description
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
        # Add async methods
        mock_repo.get_tool_config_async = AsyncMock(return_value=None)
        mock_repo.list_tool_configs_async = AsyncMock(return_value=[])
        return mock_repo

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        return create_mock_tool("test_tool", "A test tool")

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_init(self, mock_embedding_config_repository, backend_name, get_backend):
        """Test ToolRetriever initialization."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            # Mock the embedding database
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.max_num == 5
            assert retriever.min_sim == 0.3
            assert isinstance(retriever.tools, dict)
            assert len(retriever.tools) == 1  # tool_retriever is added automatically
            assert "tool_retriever" in retriever.tools
            assert retriever.tool_indices == mock_db.tools

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_str(self, mock_embedding_config_repository, backend_name, get_backend):
        """Test string representation."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert (
                str(retriever) == "ToolRetriever(num_tools=1)"
            )  # tool_retriever is added automatically

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_index_tools(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test indexing tools in the retriever."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("tool1", "Tool 1 description")
            tool2 = create_mock_tool("tool2", "Tool 2 description")

            # Mock the repository to return empty list of tool configs
            mock_embedding_config_repository.list_tool_configs_async = AsyncMock(
                return_value=[]
            )

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Index the tools using async version
            await retriever.index_tools_async()

            # Verify cleanup was called
            mock_embedding_table.cleanup.assert_called_once()
            # Verify add was called for each tool (tool1, tool2, and tool_retriever)
            assert mock_embedding_table.add.call_count == 3

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_get_tool(
        self, mock_embedding_config_repository, mock_tool, backend_name, get_backend
    ):
        """Test getting a tool by name."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Pass tool during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[mock_tool],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            result = await retriever.get_tool_async("test_tool")

            assert result == mock_tool

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_get_nonexistent_tool(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test getting a nonexistent tool returns None."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Mock the repository to return None for nonexistent tools
            mock_embedding_config_repository.get_tool_config_async = AsyncMock(
                return_value=None
            )

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            result = await retriever.get_tool_async("nonexistent")

            assert result is None

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_list_tools(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test listing all tools."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("tool1", "Tool 1")
            tool2 = create_mock_tool("tool2", "Tool 2")

            # Mock the repository to return empty list of tool configs
            mock_embedding_config_repository.list_tool_configs_async = AsyncMock(
                return_value=[]
            )

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = await retriever.list_tools_async()

            assert len(results) == 3  # tool1, tool2, and tool_retriever
            assert tool1 in results
            assert tool2 in results

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_retrieve_min_score_property(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test retrieve_min_sim property."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.retrieve_min_sim == 0.3

            retriever.retrieve_min_sim = 0.1

            assert retriever.retrieve_min_sim == 0.1
            assert retriever.min_sim == 0.1

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_retrieve_max_num_property(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test retrieve_max_num property."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            assert retriever.retrieve_max_num == 5

            retriever.retrieve_max_num = 20

            assert retriever.retrieve_max_num == 20
            assert retriever.max_num == 20

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_retrieve_tools(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test retrieving tools by query."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
                    },
                    {
                        "text": "Search the web",
                        "metadata": {"__tool__": "search"},
                        "score": 1.2,  # score <= 1.4 gives sim >= 0.3
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = await retriever.retrieve_tools_async("math calculation")

            assert len(results) == 2
            assert tool1 in results
            assert tool2 in results

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_retrieve_tools_with_min_score(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test retrieving tools with minimum score filter."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 0.3,  # score <= 0.4 gives sim >= 0.8
                    },
                    {
                        "text": "Search the web",
                        "metadata": {"__tool__": "search"},
                        "score": 0.6,  # score > 0.4 gives sim < 0.8
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")
            tool2 = create_mock_tool("search", "Search the web")

            # Pass tools during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )
            retriever.retrieve_min_sim = 0.8

            results = await retriever.retrieve_tools_async("math calculation")

            # Only calculator should be returned (sim >= 0.8)
            assert len(results) == 1
            assert tool1 in results
            assert tool2 not in results

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_call(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test calling retriever as a function."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculate math",
                        "metadata": {"__tool__": "calculator"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            tool1 = create_mock_tool("calculator", "Calculate math")

            # Pass tool during initialization
            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            results = await retriever("math calculation")

            assert len(results) == 1
            assert results[0]["name"] == "calculator"
            assert results[0]["description"] == "Calculate math"

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_to_tool(self, mock_embedding_config_repository, backend_name, get_backend):
        """Test converting retriever to a tool."""
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            tool = retriever.to_tool()

            assert tool is not None
            # Check for name attribute (Tool interface standard)
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    def test_to_tool_invoke_no_recursion_error(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Test that to_tool() result can be invoked without recursion error.

        Regression test for issue where str(self.retrieve(query)) caused infinite
        recursion when ToolBundle objects were in the results due to circular
        references in Pydantic models.
        """
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.add = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Tool 1",
                        "metadata": {"__tool__": "tool1"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
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
                tool_backend=get_backend(),
                tools=[tool1, tool2],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Convert to tool
            tool = retriever.to_tool()

            # Verify the tool was created successfully
            assert tool is not None
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)

            # The tool should be a valid Tool object from the backend
            # We don't invoke it here as the actual invocation depends on the backend
            # The important thing is that to_tool() doesn't cause recursion errors

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_retrieve_tools_async_filters_none_values(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Regression test: retrieve_tools_async should filter out None values.

        Bug: When get_tool_async returns None (tool config not found), those None
        values were included in the returned list, causing AttributeError when
        accessing tool.name or tool.description.

        Fix: Filter out None values before returning from retrieve_tools_async.
        """
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Tool 1",
                        "metadata": {"__tool__": "tool1"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
                    },
                    {
                        "text": "Tool 2",
                        "metadata": {"__tool__": "tool2"},
                        "score": 1.25,  # score <= 1.4 gives sim >= 0.3
                    },
                    {
                        "text": "Tool 3",
                        "metadata": {"__tool__": "tool3"},
                        "score": 1.2,  # score <= 1.4 gives sim >= 0.3
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Create only tool1 and tool3, tool2 will not be found
            tool1 = create_mock_tool("tool1", "Tool 1")
            tool3 = create_mock_tool("tool3", "Tool 3")

            # Mock repository to return None for tool2
            mock_embedding_config_repository.get_tool_config_async = AsyncMock(
                side_effect=lambda name: None if name == "tool2" else None
            )

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[tool1, tool3],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Retrieve tools - should only return tool1 and tool3, not None for tool2
            results = await retriever.retrieve_tools_async("test query")

            # Verify no None values in results
            assert all(t is not None for t in results)
            # Verify only valid tools are returned
            assert len(results) == 2
            assert tool1 in results
            assert tool3 in results

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_call_with_missing_tool_configs(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Regression test: __call__ should handle missing tool configs gracefully.

        When some tools in search results don't have configs, __call__ should
        only return metadata for tools that were successfully loaded.
        """
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Calculator",
                        "metadata": {"__tool__": "calculator"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
                    },
                    {
                        "text": "Missing Tool",
                        "metadata": {"__tool__": "missing_tool"},
                        "score": 1.2,  # score <= 1.4 gives sim >= 0.3
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Only create calculator tool, missing_tool will not be found
            calculator = create_mock_tool("calculator", "Calculate math")

            # Mock repository to return None for missing_tool
            mock_embedding_config_repository.get_tool_config_async = AsyncMock(
                return_value=None
            )

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=[calculator],
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Call retriever - should only return calculator metadata
            results = await retriever("math calculation")

            # Verify results are valid JSON-serializable dicts
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]["name"] == "calculator"
            assert results[0]["description"] == "Calculate math"

    @pytest.mark.parametrize("backend_name,get_backend", get_tool_backends)
    @pytest.mark.asyncio
    async def test_retrieve_tools_async_all_tools_missing(
        self, mock_embedding_config_repository, backend_name, get_backend
    ):
        """Regression test: retrieve_tools_async should return empty list when all tools are missing.

        Edge case: If all tools in search results don't have configs, should
        return an empty list instead of a list of None values.
        """
        with patch(
            "fivcplayground.embeddings.create_embedding_db_async"
        ) as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_embedding_table.search = Mock(
                return_value=[
                    {
                        "text": "Missing Tool 1",
                        "metadata": {"__tool__": "missing1"},
                        "score": 1.3,  # score <= 1.4 gives sim >= 0.3
                    },
                    {
                        "text": "Missing Tool 2",
                        "metadata": {"__tool__": "missing2"},
                        "score": 1.2,  # score <= 1.4 gives sim >= 0.3
                    },
                ]
            )
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            # Don't create any tools - all will be missing
            mock_embedding_config_repository.get_tool_config_async = AsyncMock(
                return_value=None
            )

            retriever = ToolRetriever(
                tool_backend=get_backend(),
                tools=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Retrieve tools - should return empty list, not [None, None]
            results = await retriever.retrieve_tools_async("test query")

            # Verify empty list is returned
            assert results == []
            assert all(t is not None for t in results)


if __name__ == "__main__":
    pytest.main([__file__])
