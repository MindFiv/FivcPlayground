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
from fivcplayground.tools.types.repositories import FileToolConfigRepository
from .chats import Chat, ChatManager
from .tasks import TaskManager


def _load_mcp_config():
    with utils.OutputDir():
        return tools.create_tool_loader(
            tool_retriever=tools.create_tool_retriever(),
            tool_config_repository=FileToolConfigRepository(),
            config_file="mcp.yml",
        )


default_mcp_loader = utils.LazyValue(_load_mcp_config)
