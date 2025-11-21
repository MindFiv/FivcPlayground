from typing import List, Optional, Dict

from pydantic import BaseModel, Field
from fivcplayground import embeddings
from fivcplayground.tools.types.backends import (
    Tool,
    make_tool,
    get_tool_name,
    get_tool_description,
)


class ToolRetriever(object):
    """A semantic search-based retriever for tools.

    ToolRetriever manages a collection of tools and provides semantic search capabilities
    to find the most relevant tools for a given query. It uses embeddings to create a
    searchable index of tool descriptions and supports both individual tools and ToolBundle
    objects.

    Key Features:
        - Semantic search using embeddings to find relevant tools
        - Support for both individual tools and ToolBundle objects
        - Optional bundle expansion to get individual tools from bundles
        - Configurable search parameters (max_num, min_score)
        - Proper error handling for duplicate tools and missing descriptions
        - Integration with embedding database for efficient search

    The retriever stores tools in an embedding collection indexed by their descriptions,
    allowing for semantic similarity matching rather than keyword matching.

    Attributes:
        max_num: Maximum number of tools to return in search results (default: 10)
        min_score: Minimum similarity score for search results (default: 0.0)
        tools: Dictionary mapping tool names to BaseTool instances
        collection: EmbeddingCollection for semantic search

    Example:
        >>> retriever = ToolRetriever()
        >>> retriever.add_tool(my_tool)
        >>> tools = retriever.retrieve_tools("get weather information")
        >>> tools_expanded = retriever.retrieve_tools("get weather", expand=True)
    """

    def __init__(
        self,
        embedding_config_repository: embeddings.EmbeddingConfigRepository | None = None,
        embedding_config_id: str = "default",
        **kwargs,  # ignore additional kwargs
    ):
        self.max_num = 10  # top k
        self.min_score = 0.0  # min score
        self.tools: dict[str, Tool] = {}
        db = embeddings.create_embedding_db(
            embedding_config_repository,
            embedding_config_id,
        )
        # Use dynamic attribute access to get the tools collection (EmbeddingTable)
        self.collection = db.tools
        self.collection.cleanup()  # clean up any old data

    def __str__(self):
        return f"ToolRetriever(num_tools={len(self.tools)})"

    def cleanup(self):
        self.max_num = 10  # top k
        self.min_score = 1.0  # min score
        self.tools.clear()
        self.collection.cleanup()

    def add_tool(self, tool: Tool, **kwargs):
        tool_name = get_tool_name(tool)
        if tool_name in self.tools:
            raise ValueError(f"Duplicate tool name: {tool_name}")

        tool_desc = get_tool_description(tool)
        if not tool_desc:
            raise ValueError(f"Tool description is empty: {tool_name}")

        self.collection.add(
            tool_desc,
            metadata={"__tool__": tool_name},
        )
        self.tools[tool_name] = tool

        print(f"Total Docs {self.collection.count()} in ToolRetriever")

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self.tools.values())

    def delete_tool(self, name: str):
        """
        Delete a tool from the retriever.

        Removes the tool from:
        - self.tools dictionary
        - embedding collection (by metadata)

        Args:
            name: The name of the tool to delete

        Raises:
            ValueError: If the tool doesn't exist
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        # Remove from tools dictionary
        del self.tools[name]

        self.collection.delete(metadata={"__tool__": name})
        print(
            f"Removed tool '{name}'. "
            f"Total Docs {self.collection.count()} in ToolRetriever"
        )

    @property
    def retrieve_min_score(self):
        return self.min_score

    @retrieve_min_score.setter
    def retrieve_min_score(self, value: float):
        self.min_score = value

    @property
    def retrieve_max_num(self):
        return self.max_num

    @retrieve_max_num.setter
    def retrieve_max_num(self, value: int):
        self.max_num = value

    def retrieve_tools(
        self,
        query: str,
        **kwargs,
    ) -> List[Tool]:
        """Retrieve tools for a query using semantic search.

        Performs semantic search on tool descriptions using embeddings to find the most
        relevant tools for the given query. Supports optional bundle expansion to get
        individual tools from ToolBundle objects.

        Search Process:
            1. Searches the embedding collection for similar tool descriptions
            2. Filters results by minimum score threshold (retrieve_min_score)
            3. Limits results to maximum number (retrieve_max_num)
            4. Optionally expands ToolBundle objects into individual tools

        Args:
            query: The query string describing the desired tool functionality
            expand: Whether to expand ToolBundle objects into individual tools
                   - False (default): Returns bundles as-is
                   - True: Expands bundles to return all contained tools
            **kwargs: Additional keyword arguments (ignored)

        Returns:
            List of BaseTool instances matching the query, sorted by relevance

        Example:
            >>> retriever.retrieve_tools("get weather")  # Returns bundles
            >>> retriever.retrieve_tools("get weather", expand=True)  # Returns individual tools

        Note:
            - Results are filtered by retrieve_min_score
            - Limited to retrieve_max_num results
            - Bundle expansion is useful when you need individual tools
            - Without expansion, bundles can be used to group related tools
        """
        sources = self.collection.search(
            query,
            num_documents=self.retrieve_max_num,
        )

        tool_names = set(
            src["metadata"]["__tool__"]
            for src in sources
            if src["score"] >= self.retrieve_min_score
        )

        return [self.get_tool(name) for name in tool_names]

    def __call__(self, *args, **kwargs) -> List[Dict]:
        tools = self.retrieve_tools(*args, **kwargs)
        return [
            {"name": get_tool_name(t), "description": get_tool_description(t)}
            for t in tools
        ]

    class _ToolSchema(BaseModel):
        query: str = Field(description="The task to find the best tool for")

    def to_tool(self):
        """Convert the retriever to a LangChain tool.

        Creates a LangChain tool that wraps the retrieve_tools() method, allowing the retriever
        to be used as a tool within agent systems. The tool returns a string representation
        of the retrieved tools.

        Returns:
            A LangChain tool that can be used in agent systems

        Example:
            >>> retriever = ToolRetriever()
            >>> tool = retriever.to_tool()
            >>> # Use tool in an agent
            >>> agent.tools.append(tool)

        Note:
            - The returned tool uses retrieve_tools() without expand parameter
            - Results are converted to string for compatibility
            - Useful for creating a "tool discovery" tool in agent systems
        """

        @make_tool
        def tool_retriever(query: str) -> str:
            """Use this tool to retrieve the best tools for a given task"""
            # Use __call__ to get tool metadata (name and description) instead of
            # the full BaseTool objects, which can cause infinite recursion when
            # converting to string due to circular references in Pydantic models
            return str(self(query))

        return tool_retriever
