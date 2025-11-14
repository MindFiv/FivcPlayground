import asyncio
import os
from typing import Optional

from fivcplayground.tools.types.backends import (
    ToolsBundle,
    get_tool_name,
    get_tool_description,
    set_tool_description,
)
from fivcplayground.tools.types.configs import ToolsConfig
from fivcplayground.tools.types.retrievers import ToolsRetriever


class ToolsLoader(object):
    """Loader for MCP tools using langchain-mcp-adapters.

    ToolsLoader manages the complete lifecycle of loading tools from MCP (Model Context Protocol)
    servers configured in ToolsConfig and registering them with a ToolsRetriever. It provides
    both synchronous and asynchronous interfaces for loading and cleaning up tools.

    Key Features:
        - Loads tools from multiple MCP servers configured in a YAML file
        - Organizes tools into ToolsBundle objects for better management
        - Supports incremental updates: automatically adds new bundles and removes old ones
        - Maintains a persistent MCP client for efficient resource usage
        - Provides proper async context management for session lifecycle
        - Handles errors gracefully, continuing to load other bundles if one fails

    The loader tracks which tools belong to which bundle, allowing for efficient cleanup
    and updates when the configuration changes.

    Attributes:
        config: ToolsConfig instance for loading MCP server configurations
        tools_retriever: ToolsRetriever instance to register tools with
        tools_bundles: Dictionary mapping bundle names (server names) to sets of tool names
                      Example: {"weather_server": {"get_weather", "get_forecast"}}
        client: Persistent MultiServerMCPClient instance for connecting to MCP servers

    Example:
        >>> retriever = ToolsRetriever()
        >>> loader = ToolsLoader(tools_retriever=retriever, config_file="mcp.yaml")
        >>> await loader.load_async()  # Load all configured tools
        >>> # ... use tools ...
        >>> await loader.cleanup_async()  # Clean up resources
    """

    def __init__(
        self,
        tools_retriever: Optional[ToolsRetriever] = None,
        config_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the tools loader.

        Args:
            tools_retriever: The ToolsRetriever instance to register tools with
            config_file: Path to MCP configuration file (defaults to mcp.yaml).
                        If not provided, uses MCP_FILE environment variable or "mcp.yaml"
            **kwargs: Additional arguments (ignored)

        Raises:
            AssertionError: If tools_retriever is None
        """
        assert tools_retriever is not None
        # Use provided config_file or get from environment
        if config_file is None:
            config_file = os.environ.get("MCP_FILE", "mcp.yaml")
        config_file = os.path.abspath(config_file)

        # Initialize config with load=False to defer loading until load_async() is called
        self.config = ToolsConfig(config_file=config_file, load=False)
        self.tools_retriever = tools_retriever
        # Track tools by bundle for incremental updates
        self.tools_bundles: dict[str, set[str]] = {}

    async def load_async(self):
        """Load tools from configured MCP servers and register them asynchronously.

        This method performs the complete loading process:

        1. Loads configuration from the YAML file
        2. Creates a persistent MultiServerMCPClient for all configured servers
        3. Determines which bundles are new and which should be removed
        4. Removes tools from bundles that are no longer in the configuration
        5. Loads tools from new bundles and wraps them in ToolsBundle objects
        6. Registers each ToolsBundle with the ToolsRetriever

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
        self.config.load()
        errors = self.config.get_errors()
        if errors:
            # print(f"Errors loading config: {errors}")
            return

        # Create persistent client (kept alive during app runtime)
        connections = {
            server_name: self.config.get(server_name).value
            for server_name in self.config.list()
        }
        bundle_names_target = set(connections.keys())
        bundle_names_now = set(self.tools_bundles.keys())

        bundle_names_to_remove = bundle_names_now - bundle_names_target
        bundle_names_to_add = bundle_names_target - bundle_names_now

        # Remove tools from bundles that are no longer configured
        for bundle_name in bundle_names_to_remove:
            self.tools_bundles.pop(bundle_name, None)
            self.tools_retriever.remove(bundle_name)

        # Load tools for new bundles using proper async context management
        for bundle_name in bundle_names_to_add:
            try:
                # Use async with for proper session lifecycle management
                bundle = ToolsBundle(bundle_name, connections[bundle_name])
                async with bundle.load_async() as tools:
                    tool_names = {get_tool_name(t) for t in tools}
                    tool_descriptions = [get_tool_description(t) for t in tools]
                    set_tool_description(bundle, "\n\n".join(tool_descriptions))

                self.tools_retriever.add(bundle)
                self.tools_bundles.setdefault(bundle_name, tool_names)

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

        1. Removes all loaded tool bundles from the ToolsRetriever
        2. Clears the tools_bundles tracking dictionary
        3. Releases the MCP client reference

        This should be called when the application is shutting down to ensure
        proper resource cleanup and prevent resource leaks.

        Note:
            - Removes bundles by their bundle name (server name)
            - Clears all internal state tracking
            - Does not explicitly close the MCP client (handled by garbage collection)
        """
        # Remove all tracked tools from the retriever
        for bundle_name in self.tools_bundles.keys():
            self.tools_retriever.remove(bundle_name)

        # Clear the bundle tracking and client reference
        self.tools_bundles.clear()

    def cleanup(self):
        """Synchronous cleanup wrapper for cleanup_async.

        This is a convenience method for synchronous contexts.
        """
        asyncio.run(self.cleanup_async())
