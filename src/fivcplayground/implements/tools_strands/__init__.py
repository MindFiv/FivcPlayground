"""
Tool implementations for FivcPlayground using Strands framework.

This module provides implementations of ITool, IToolProvider, and related
interfaces, enabling flexible tool creation and management through the component architecture.

Classes:
    ToolImpl: Implementation of ITool interface for Strands tools
    ToolBundleImpl: Implementation of IToolBundle interface for tool bundles
    ToolProviderImpl: Implementation of IToolProvider interface for tool retrieval from embeddings and settings
    CalculatorToolImpl: Implementation of ITool interface for calculator tool
    ClockToolImpl: Implementation of ITool interface for clock tool
"""

__all__ = [
    "ToolImpl",
    "ToolBundleImpl",
    "ToolProviderImpl",
    "CalculatorToolImpl",
    "ClockToolImpl",
]

import logging
from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional, List, AsyncGenerator

from fivcglue import IComponentSite
from fivcglue.interfaces.utils import query_component

from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from strands.tools.mcp import MCPClient

from fivcplayground.interfaces import (
    ITool,
    IToolBundle,
    IToolProvider,
    # ISetting,
    ISettingProvider,
    IEmbeddingDBProvider,
    # IEmbeddingDB,
    EmbeddingDoc,
)

# Import tool implementations
from .calculator import CalculatorToolImpl
from .clock import ClockToolImpl

logger = logging.getLogger(__name__)


class ToolImpl(ITool):
    """
    Implementation of ITool interface with lazy loading support.

    This class represents a single tool instance with metadata and
    lazy-loaded access to the underlying tool object. The actual tool
    instantiation is deferred until get_underlying() is first called.

    Example:
        >>> tool = ToolImpl("calculator", underlying_tool=calc_tool)
        >>> tool.name
        'calculator'
        >>> underlying = tool.get_underlying()  # Returns the tool
    """

    def __init__(self, name: str, description: str = "", underlying: Any = None):
        """
        Initialize a tool instance with lazy loading.

        Args:
            name: Name of the tool (e.g., "calculator", "weather")
            description: Description of what the tool does
            underlying: The underlying tool object (Strands Tool)
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
        Get the underlying tool object.

        Returns:
            The underlying tool instance (Strands Tool)
        """
        return self._underlying


class ToolBundleImpl(IToolBundle):
    """
    Implementation of IToolBundle interface for MCP server tool bundles.

    This class represents a bundle of tools from an MCP (Model Context Protocol) server.
    It wraps the MCP server connection configuration and provides async setup to load
    the actual tools from the server.

    Example:
        >>> bundle = ToolBundleImpl(
        ...     name="weather_server",
        ...     description="Weather tools",
        ...     connection_config={"command": "python weather_server.py"}
        ... )
        >>> async with bundle.setup_async() as tools:
        ...     for tool in tools:
        ...         print(tool.name)
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        connection_config: Optional[dict] = None,
    ):
        """
        Initialize a tool bundle for an MCP server.

        Args:
            name: Name of the MCP server (e.g., "weather_server")
            description: Description of the tool bundle
            connection_config: MCP server connection configuration dict with either:
                - "command": Command to run the server
                - "url": URL for SSE-based server
                Plus optional "args" and "env" for command-based servers
        """
        self._name = name
        self._description = description
        self._connection_config = connection_config or {}
        self._tools_cache: Optional[List[ITool]] = None

    @property
    def name(self) -> str:
        """Get the name of the tool bundle."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the tool bundle."""
        return self._description

    @asynccontextmanager
    async def setup_async(self) -> AsyncGenerator[List[ITool], None]:
        """
        Load tools from the MCP server asynchronously.

        This method connects to the MCP server using the connection configuration,
        retrieves the list of available tools, and yields them as ITool instances.

        Supports both stdio (command-based) and SSE (URL-based) MCP servers.

        Yields:
            List of ITool instances from the MCP server

        Raises:
            ValueError: If connection_config is missing or invalid
            Exception: If connection to MCP server fails
        """
        if not self._connection_config:
            raise ValueError(
                f"Cannot setup bundle '{self._name}': no connection configuration"
            )

        try:
            # Load tools from MCP server
            async with self._load_mcp_tools_async() as tools:
                # Convert Strands tools to ITool instances
                tool_impls: List[ITool] = []
                tool_descriptions = []

                for tool in tools:
                    # Extract tool name and description from Strands tool
                    tool_name = self._get_tool_name(tool)
                    tool_desc = self._get_tool_description(tool)
                    tool_descriptions.append(tool_desc)

                    # Create ToolImpl for each tool from the bundle
                    tool_impl = ToolImpl(
                        name=tool_name,
                        description=tool_desc,
                        underlying=tool,
                    )
                    tool_impls.append(tool_impl)

                # Cache the tools
                self._tools_cache = tool_impls

                # Yield the tools
                yield tool_impls

        except Exception as e:
            logger.error(f"Error loading tools from MCP server '{self._name}': {e}")
            raise

    @asynccontextmanager
    async def _load_mcp_tools_async(self) -> AsyncGenerator[List[Any], None]:
        """
        Load tools from MCP server using the connection configuration.

        Supports both stdio (command-based) and SSE (URL-based) MCP servers.

        Yields:
            List of Strands Tool instances from the MCP server

        Raises:
            ValueError: If connection config is invalid
            Exception: If connection to MCP server fails
        """
        # Create MCP client based on connection type
        if "command" in self._connection_config:
            # Stdio-based MCP server (command-based)
            client_context = stdio_client(
                StdioServerParameters(**self._connection_config)
            )
        else:
            # SSE-based MCP server (URL-based)
            # Remove transport field if present (not needed for SSE)
            config = dict(self._connection_config)
            config.pop("transport", None)
            client_context = sse_client(**config)

        # Use MCPClient to manage the connection
        with MCPClient(lambda: client_context) as client:
            # List all tools from the MCP server
            tools = client.list_tools_sync()
            yield list(tools)

    @staticmethod
    def _get_tool_name(tool: Any) -> str:
        """
        Extract the name from a Strands tool.

        Args:
            tool: A Strands AgentTool instance

        Returns:
            The tool name
        """
        return tool.tool_name

    @staticmethod
    def _get_tool_description(tool: Any) -> str:
        """
        Extract the description from a Strands tool.

        Args:
            tool: A Strands AgentTool instance

        Returns:
            The tool description, or empty string if not available
        """
        return tool.tool_spec.get("description") or ""


class ToolProviderImpl(IToolProvider):
    """
    Implementation of IToolProvider interface for MCP server tool bundles.

    This class provides access to tool bundles from MCP servers configured in settings.
    Each setting represents an MCP server configuration. The retriever creates ToolBundleImpl
    instances that wrap the MCP server configurations and can be set up asynchronously
    to load the actual tools.

    The settings are expected to be ISetting instances with MCP server configurations.
    The embedding is used for semantic search over tool bundles.

    Example:
        >>> from fivcglue.implements.utils import ComponentSite
        >>> from fivcplayground.interfaces import ISettingProvider, IEmbeddingDBProvider
        >>> site = ComponentSite()
        >>> # Register providers...
        >>> provider = ToolProviderImpl(site)
        >>> bundle = provider.get_tool("weather_server")
        >>> if bundle:
        ...     print(f"Bundle: {bundle.name}")
        ...     async with bundle.setup_async() as tools:
        ...         for tool in tools:
        ...             print(f"  Tool: {tool.name}")
    """

    def __init__(
        self,
        component_site: IComponentSite,
        **kwargs: Any,
    ):
        """
        Initialize the tool provider.

        Args:
            component_site: An IComponentSite instance for component registration and resolution
            **kwargs: Additional keyword arguments (unused, for compatibility)
        """
        # Try to get named setting provider first, fall back to default
        self._setting_provider = query_component(
            component_site,
            ISettingProvider,
            "tools",
        )
        if self._setting_provider is None:
            self._setting_provider = query_component(
                component_site,
                ISettingProvider,
            )

        # Try to get named embedding provider first, fall back to default
        self._embedding_provider = query_component(
            component_site,
            IEmbeddingDBProvider,
            "embeddings",
        )
        if self._embedding_provider is None:
            self._embedding_provider = query_component(
                component_site,
                IEmbeddingDBProvider,
            )

        # Retrieve embeddings and settings
        self._embedding = None
        if self._embedding_provider is not None:
            self._embedding = self._embedding_provider.get_embedding_db(
                "tools",
                user_id=None,
                **kwargs,
            )

        settings = []
        if self._setting_provider is not None:
            settings = list(
                self._setting_provider.list_settings(
                    user_id=None,
                    **kwargs,
                )
            )

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
                EmbeddingDoc(
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
        Get a tool bundle instance by name with lazy loading.

        Retrieves the MCP server configuration from settings and returns a ToolBundleImpl
        instance. Each setting represents an MCP server configuration. ToolBundleImpl
        instances are cached to avoid redundant configuration lookups.

        Args:
            name: Name of the MCP server to retrieve (e.g., "weather_server")
            **kwargs: Additional configuration parameters (overrides settings)

        Returns:
            A ToolBundleImpl instance if the tool exists, None otherwise.
            Returns None if the tool name is not found in settings.
        """
        # Check cache first
        if name in self._tools_cache:
            return self._tools_cache[name]

        # Get MCP server configuration from settings
        setting = self._settings.get(name)
        if setting is None:
            return None

        # Extract MCP server configuration from setting
        try:
            config = dict(setting.list())
            description = config.get("description", "")

            # Allow kwargs to override settings
            if "description" in kwargs:
                description = kwargs["description"]

            # Extract connection config (all keys except "description")
            connection_config = {k: v for k, v in config.items() if k != "description"}

            # Create and cache the tool bundle
            bundle = ToolBundleImpl(
                name=name,
                description=description,
                connection_config=connection_config,
            )
            self._tools_cache[name] = bundle
            return bundle
        except (ValueError, TypeError, AttributeError):
            # Re-raise configuration errors
            raise

    def list_tools(
        self,
        user_id: str | None = None,
        names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """
        List all tool bundles or specific bundles by name.

        Args:
            user_id: Optional user ID for multi-user support (unused in this implementation)
            names: Optional list of MCP server names to retrieve. If None, returns all bundles.
            **kwargs: Additional keyword arguments (unused)

        Returns:
            An iterable of ToolBundleImpl instances (each representing an MCP server)
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
        user_id: str | None = None,
        **kwargs: Any,
    ) -> Iterable[ITool]:
        """
        Search for tool bundles using semantic search or keyword matching.

        First attempts semantic search using embeddings. If embeddings are not
        available or return no results, falls back to keyword search on bundle
        names and descriptions.

        Args:
            user_id: Optional user ID for multi-user support (unused in this implementation)
            query: The search query string
            **kwargs: Additional keyword arguments (unused)

        Returns:
            An iterable of matching ToolBundleImpl instances
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
