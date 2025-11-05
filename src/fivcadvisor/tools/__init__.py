__all__ = [
    "register_default_tools",
    "default_retriever",
    "default_loader",
    "ToolsConfig",
    "ToolsRetriever",
    "ToolsLoader",
]

from typing import Optional

from fivcadvisor.utils import create_lazy_value
from fivcadvisor.tools.types import (
    ToolsRetriever,
    ToolsConfig,
    ToolsLoader,
)
from fivcadvisor.tools.types.backends import get_tool_name
from fivcadvisor.tools.clock import clock


def register_default_tools(tools_retriever: Optional[ToolsRetriever] = None, **kwargs):
    """
    Register default tools with the tools retriever.

    Registers built-in tools like clock tools. Additional tools are loaded
    from MCP servers using ToolsLoader.

    Args:
        tools_retriever: The ToolsRetriever instance to register tools with
        **kwargs: Additional arguments (ignored)

    Returns:
        List of registered tools
    """
    assert tools_retriever is not None

    # Register clock tool
    tools = [clock]
    tools_retriever.add_batch(tools)

    return tools


def _load_retriever() -> ToolsRetriever:
    """Load and initialize the default tools retriever.

    This creates a ToolsRetriever and loads MCP tools from configured servers.
    """
    retriever = ToolsRetriever()
    register_default_tools(tools_retriever=retriever)

    # # Load MCP tools using ToolsLoader
    # loader = ToolsLoader(tools_retriever=retriever)
    # loader.load()

    print(f"Registered Tools: {[get_tool_name(t) for t in retriever.get_all()]}")
    return retriever


default_retriever = create_lazy_value(_load_retriever)
default_loader = create_lazy_value(
    lambda: ToolsLoader(tools_retriever=default_retriever)
)
