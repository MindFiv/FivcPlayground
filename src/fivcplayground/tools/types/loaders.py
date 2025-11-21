import asyncio

from fivcplayground.tools.types.backends import (
    ToolBundle,
    get_tool_name,
    get_tool_description,
    set_tool_description,
)

from fivcplayground.tools.types.repositories import ToolConfigRepository
from fivcplayground.tools.types.retrievers import ToolRetriever


class ToolLoader(object):
    """Loader for MCP tools using langchain-mcp-adapters.

    ToolLoader manages the complete lifecycle of loading tools from MCP (Model Context Protocol)
    servers configured in ToolConfigRepository and registering them with a ToolRetriever. It provides
    both synchronous and asynchronous interfaces for loading and cleaning up tools.

    Key Features:
        - Loads tools from multiple MCP servers configured in a repository
        - Organizes tools into ToolBundle objects for better management
        - Supports incremental updates: automatically adds new bundles and removes old ones
        - Maintains a persistent MCP client for efficient resource usage
        - Provides proper async context management for session lifecycle
        - Handles errors gracefully, continuing to load other bundles if one fails

    The loader tracks which tools belong to which bundle, allowing for efficient cleanup
    and updates when the configuration changes.

    Attributes:
        tool_config_repository: ToolConfigRepository instance for loading MCP server configurations
        tool_retriever: ToolRetriever instance to register tools with
        tool_bundles: Dictionary mapping bundle names (server names) to sets of tool names
                      Example: {"weather_server": {"get_weather", "get_forecast"}}
        client: Persistent MultiServerMCPClient instance for connecting to MCP servers

    Example:
        >>> from fivcplayground.tools import create_tool_loader, create_tool_retriever
        >>> from fivcplayground.tools.types.repositories import FileToolConfigRepository
        >>> retriever = create_tool_retriever()
        >>> repo = FileToolConfigRepository()
        >>> loader = create_tool_loader(tool_retriever=retriever, tool_config_repository=repo)
        >>> await loader.load_async()  # Load all configured tools
        >>> # ... use tools ...
        >>> await loader.cleanup_async()  # Clean up resources
    """

    def __init__(
        self,
        tool_retriever: ToolRetriever | None = None,
        tool_config_repository: ToolConfigRepository | None = None,
        **kwargs,
    ):
        """Initialize the tools loader.

        Args:
            tool_retriever: The ToolRetriever instance to register tools with
            config_file: Path to MCP configuration file (defaults to mcp.yaml).
                        If not provided, uses MCP_FILE environment variable or "mcp.yaml"
            **kwargs: Additional arguments (ignored)

        Raises:
            AssertionError: If tool_retriever is None
        """
        assert tool_retriever is not None
        assert tool_config_repository is not None

        if tool_config_repository is None:
            from fivcplayground.tools.types.repositories.files import (
                FileToolConfigRepository,
            )

            tool_config_repository = FileToolConfigRepository()

        self.tool_config_repository = tool_config_repository
        self.tool_retriever = tool_retriever
        # Track tools by bundle for incremental updates
        self.tool_bundles: dict[str, set[str]] = {}

    async def load_async(self):
        """Load tools from configured MCP servers and register them asynchronously.

        This method performs the complete loading process:

        1. Loads configuration from the YAML file
        2. Creates a persistent MultiServerMCPClient for all configured servers
        3. Determines which bundles are new and which should be removed
        4. Removes tools from bundles that are no longer in the configuration
        5. Loads tools from new bundles and wraps them in ToolBundle objects
        6. Registers each ToolBundle with the ToolRetriever

        Incremental Updates:
            - Only loads tools from newly configured servers
            - Only removes tools from servers that are no longer configured
            - Preserves existing tools from unchanged servers

        Error Handling:
            - Prints configuration errors but continues execution
            - Catches exceptions when loading individual bundles
            - Continues loading other bundles even if one fails
            - Prints error messages for failed bundles

        Note:
            - Sessions are managed within async contexts for proper lifecycle
            - The MCP client is stored persistently for the application lifetime
            - Empty bundles (servers with no tools) are skipped
        """
        # Create persistent client (kept alive during app runtime)
        tool_configs = {
            tool_config.id: tool_config
            for tool_config in self.tool_config_repository.list_tool_configs()
        }
        bundle_names_target = set(tool_configs.keys())
        bundle_names_now = set(self.tool_bundles.keys())

        bundle_names_to_remove = bundle_names_now - bundle_names_target
        bundle_names_to_add = bundle_names_target - bundle_names_now

        # Remove tools from bundles that are no longer configured
        for bundle_name in bundle_names_to_remove:
            self.tool_bundles.pop(bundle_name, None)
            self.tool_retriever.delete_tool(bundle_name)

        # Load tools for new bundles using proper async context management
        for bundle_name in bundle_names_to_add:
            try:
                # Use async with for proper session lifecycle management
                bundle = ToolBundle(tool_configs[bundle_name])
                async with bundle.load_async() as tools:
                    tool_names = {get_tool_name(t) for t in tools}
                    tool_descriptions = [get_tool_description(t) for t in tools]
                    set_tool_description(bundle, "\n\n".join(tool_descriptions))

                self.tool_retriever.add_tool(bundle)
                self.tool_bundles.setdefault(bundle_name, tool_names)

            except Exception as e:
                print(f"Error loading tools from {bundle_name}: {e}")
                continue

    def load(self):
        """Load tools synchronously.

        This is a convenience method that handles event loop management
        for synchronous contexts.
        """
        asyncio.run(self.load_async())

    async def cleanup_async(self):
        """Asynchronously clean up MCP resources and state.

        This method performs complete cleanup:

        1. Removes all loaded tool bundles from the ToolRetriever
        2. Clears the tool_bundles tracking dictionary
        3. Releases the MCP client reference

        This should be called when the application is shutting down to ensure
        proper resource cleanup and prevent resource leaks.

        Note:
            - Removes bundles by their bundle name (server name)
            - Clears all internal state tracking
            - Does not explicitly close the MCP client (handled by garbage collection)
        """
        # Remove all tracked tools from the retriever
        for bundle_name in self.tool_bundles.keys():
            self.tool_retriever.delete_tool(bundle_name)

        # Clear the bundle tracking and client reference
        self.tool_bundles.clear()

    def cleanup(self):
        """Synchronous cleanup wrapper for cleanup_async.

        This is a convenience method for synchronous contexts.
        """
        asyncio.run(self.cleanup_async())
