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
]

from .chats import Chat, ChatManager
from .tasks import TaskManager
