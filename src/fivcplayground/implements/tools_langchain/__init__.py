"""
Tool implementations for FivcPlayground using LangChain framework.

This module provides implementations of ITool, IToolRetriever, and IToolRetrieverProvider
interfaces, enabling flexible LangChain tool creation and management through the component architecture.

Classes:
    ToolImpl: Implementation of ITool interface for LangChain tools
    ToolRetrieverImpl: Implementation of IToolRetriever interface for tool retrieval from embeddings and settings
    ToolRetrieverProviderImpl: Implementation of IToolRetrieverProvider interface for creating tool retrievers
"""

import logging
from typing import Any, Iterable, Optional, List

from fivcglue import IComponentSite
from fivcglue.interfaces.utils import query_component

from fivcplayground.interfaces import (
    ITool,
    IToolRetriever,
    IToolRetrieverProvider,
    ISetting,
    ISettingProvider,
    IEmbeddingDBProvider,
    IEmbeddingDB,
    IEmbeddingDoc,
)

logger = logging.getLogger(__name__)


class ToolImpl(ITool):
    """
    Implementation of ITool interface with lazy loading support for LangChain tools.

    This class represents a single LangChain tool instance with metadata and
    lazy-loaded access to the underlying tool object. The actual tool
    instantiation is deferred until get_underlying() is first called.

    Example:
        >>> tool = ToolImpl("calculator", description="Math tool", underlying=calc_tool)
        >>> tool.name
        'calculator'
        >>> underlying = tool.get_underlying()  # Returns the LangChain tool
    """

    def __init__(self, name: str, description: str = "", underlying: Any = None):
        """
        Initialize a tool instance with lazy loading.

        Args:
            name: Name of the tool (e.g., "calculator", "weather")
            description: Description of what the tool does
            underlying: The underlying LangChain tool object
        """
        self._name = name
        self._description = description
        self._underlying = underlying

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._description

    def get_underlying(self) -> Any:
        """
        Get the underlying LangChain tool object.

        Returns:
            The underlying LangChain tool instance
        """
        return self._underlying


class ToolRetrieverImpl(IToolRetriever):
    """
    Implementation of IToolRetriever interface for LangChain tools.

    This class provides access to LangChain tools configured in settings.
    Each setting represents a tool configuration. The retriever creates ToolImpl
    instances that wrap the LangChain tools and can be retrieved by name or searched.

    The embedding is used for semantic search over tool names and descriptions.

    Example:
        >>> retriever = ToolRetrieverImpl(embedding, settings)
        >>> tool = retriever.get_tool("calculator")
        >>> if tool:
        ...     print(f"Tool: {tool.name}")
    """

    def __init__(
        self,
        embedding: IEmbeddingDB,
        settings: List[ISetting],
        **kwargs: Any,
    ):
        """
        Initialize the tool retriever.

        Args:
            embedding: An IEmbeddingDB instance for semantic search
            settings: A list of ISetting instances containing tool configurations
            **kwargs: Additional keyword arguments (unused, for compatibility)
        """
        self._embedding = embedding
        self._settings = {s.name: s for s in settings}  # Index settings by name
        self._tools_cache = {}  # Cache for created tools
        self._tools_indexed = False  # Track if tools have been indexed in embeddings

    def _index_tools_in_embeddings(self) -> None:
        """Index all tools in embeddings for semantic search."""
        if self._tools_indexed or self._embedding is None:
            return

        # Get all tools and index them
        for tool in self.list_tools():
            self._embedding.add_document(
                IEmbeddingDoc(
                    text=f"{tool.name}: {tool.description}",
                    metadata={"tool_name": tool.name},
                )
            )
        self._tools_indexed = True

    def get_tool(
        self,
        name: str,
        **kwargs: Any,
    ) -> ITool | None:
        """
        Get a tool instance by name with lazy loading.

        Retrieves the tool configuration from settings and returns a ToolImpl
        instance. ToolImpl instances are cached to avoid redundant configuration lookups.

        Args:
            name: Name of the tool to retrieve (e.g., "calculator")
            **kwargs: Additional configuration parameters (overrides settings)

        Returns:
            A ToolImpl instance if the tool exists, None otherwise.
        """
        # Check cache first
        if name in self._tools_cache:
            return self._tools_cache[name]

        # Get tool configuration from settings
        setting = self._settings.get(name)
        if setting is None:
            return None

        # Extract tool configuration from setting
        try:
            config = dict(setting.list())
            description = config.get("description", "")

            # Allow kwargs to override settings
            if "description" in kwargs:
                description = kwargs["description"]

            # Create and cache the tool
            tool = ToolImpl(
                name=name,
                description=description,
                underlying=None,  # LangChain tool would be created here if needed
            )
            self._tools_cache[name] = tool
            return tool
        except (ValueError, TypeError, AttributeError):
            # Re-raise configuration errors
            raise

    def list_tools(
        self,
        names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """
        List all tools or specific tools by name.

        Args:
            names: Optional list of tool names to retrieve. If None, returns all tools.
            **kwargs: Additional keyword arguments (unused)

        Returns:
            An iterable of ToolImpl instances
        """
        if names is not None:
            # Get specific tools by name
            for name in names:
                tool = self.get_tool(name, **kwargs)
                if tool is not None:
                    yield tool
        else:
            # Get all tools from settings
            for name in self._settings.keys():
                tool = self.get_tool(name, **kwargs)
                if tool is not None:
                    yield tool

    def search_tools(
        self,
        query: str,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """
        Search for tools using semantic search or keyword matching.

        First attempts semantic search using embeddings. If embeddings are not
        available or return no results, falls back to keyword search on tool
        names and descriptions.

        Args:
            query: The search query string
            **kwargs: Additional keyword arguments (unused)

        Returns:
            An iterable of matching ToolImpl instances
        """
        tool_names = set()

        # Try semantic search first
        if self._embedding is not None:
            # Index tools if not already done
            if not self._tools_indexed:
                self._index_tools_in_embeddings()

            # Search embeddings
            results = self._embedding.search_documents(query, num_documents=10)
            for result in results:
                if hasattr(result, "metadata") and "tool_name" in result.metadata:
                    tool_names.add(result.metadata["tool_name"])

        # If no results from embeddings, fall back to keyword search
        if not tool_names:
            query_lower = query.lower()
            for tool in self.list_tools():
                if (
                    query_lower in tool.name.lower()
                    or query_lower in tool.description.lower()
                ):
                    tool_names.add(tool.name)

        # Return matching tools
        for tool_name in tool_names:
            tool = self.get_tool(tool_name)
            if tool is not None:
                yield tool


class ToolRetrieverProviderImpl(IToolRetrieverProvider):
    """
    Implementation of IToolRetrieverProvider interface for LangChain tools.

    This class provides access to tool retrievers configured through the settings provider.
    It loads tool configurations from settings and creates tool retriever instances on demand.

    Example:
        >>> from fivcplayground.settings import default_component_site
        >>> from fivcplayground.interfaces import IToolRetrieverProvider
        >>> provider = default_component_site.get_component(IToolRetrieverProvider)
        >>> retriever = provider.get_retriever()
        >>> if retriever:
        ...     tool = retriever.get_tool("calculator")
    """

    def __init__(self, component_site: IComponentSite, **kwargs: Any):
        """
        Initialize the tool retriever provider.

        Args:
            component_site: An IComponentSite instance for component registration
            **kwargs: Additional keyword arguments (unused, for compatibility)
        """
        self._setting_provider = query_component(
            component_site,
            ISettingProvider,
            "tools",
        )
        self._embedding_provider = query_component(
            component_site,
            IEmbeddingDBProvider,
            "embeddings",
        )

    def get_retriever(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> IToolRetriever | None:
        """
        Get a tool retriever instance.

        Retrieves tool settings and embeddings, then creates a ToolRetrieverImpl
        instance. Returns None if settings or embeddings are not available.

        Args:
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional keyword arguments (unused)

        Returns:
            A ToolRetrieverImpl instance if settings and embeddings are available, None otherwise.
        """
        settings = self._setting_provider.list_settings(
            user_id=user_id,
            **kwargs,
        )
        settings = list(s for s in settings)
        embeddings = self._embedding_provider.get_embedding_db(
            "tools",
            user_id=user_id,
            **kwargs,
        )
        if not embeddings or not settings:
            return None

        return ToolRetrieverImpl(embeddings, settings, **kwargs)
