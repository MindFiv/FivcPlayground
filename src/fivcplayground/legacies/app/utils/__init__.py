"""
Utils module for FivcPlayground app.

This module provides utility classes for handling application state:
- Chat: Manages chat conversation and agent execution
- ChatManager: Manages multiple chat instances
- TaskManager: Manages task execution with UI notifications
"""

__all__ = [
    "Chat",
    "ChatManager",
    "TaskManager",
    "default_mcp_loader",
]

from fivcplayground import utils, tools
from .chats import Chat, ChatManager
from .tasks import TaskManager


def _load_mcp_config():
    with utils.OutputDir():
        return tools.ToolsLoader(
            tools_retriever=tools.default_retriever,
            config_file="mcp.yml",
        )


default_mcp_loader = utils.LazyValue(_load_mcp_config)
