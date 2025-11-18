"""
FivcPlayground App Views

View implementations for the multi-page application.
Each view inherits from ViewBase and implements the render() method.
"""

__all__ = [
    "ViewBase",
    "ViewNavigation",
    "ChatView",
    "TaskView",
    "GeneralSettingView",
    "MCPSettingView",
]

from .base import ViewBase, ViewNavigation
from .chats import ChatView
from .tasks import TaskView
from .settings import GeneralSettingView, MCPSettingView  # noqa: F401
