"""
Settings Views

View implementations for application settings and configuration.
"""

__all__ = [
    "GeneralSettingView",
    "MCPSettingView",
]

from .general import GeneralSettingView
from .mcp import MCPSettingView
