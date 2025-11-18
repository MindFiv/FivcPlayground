"""
FivcPlayground Streamlit Web Application

A modern, interactive Streamlit interface for FivcPlayground with Agent chat functionality.
Multi-page application with dynamic navigation.
"""

__all__ = [
    "main",
]

import streamlit as st
import nest_asyncio

from fivcplayground.tools import default_retriever
from fivcplayground.agents.types.repositories import (
    # FileAgentsRuntimeRepository,
    SqliteAgentsRuntimeRepository,
)
from fivcplayground.app.utils import ChatManager, default_mcp_loader
from fivcplayground.app.views import (
    ViewNavigation,
    ChatView,
    TaskView,
    MCPSettingView,
    GeneralSettingView,
)

# Apply nest_asyncio to allow nested event loops in Streamlit context
nest_asyncio.apply()


def main():
    """Main Streamlit application entry point with custom ViewNavigation"""
    default_mcp_loader.load()
    # Page configuration (must be called first)
    st.set_page_config(
        page_title="FivcPlayground - Intelligent Agent Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    agent_runtime_repo = SqliteAgentsRuntimeRepository()
    # agent_runtime_repo = FileAgentsRuntimeRepository()
    chat_manager = ChatManager(
        agent_runtime_repo=agent_runtime_repo,
        tools_retriever=default_retriever,
    )

    # Create navigation instance
    nav = ViewNavigation()

    # Build chat views
    chat_pages = [ChatView(chat_manager.add_chat())]
    chat_pages.extend([ChatView(chat) for chat in chat_manager.list_chats()])

    # Add sections to navigation
    nav.add_section("Chats", chat_pages)
    nav.add_section(
        "Tasks",
        [TaskView()],
    )
    nav.add_section(
        "Settings",
        [GeneralSettingView(), MCPSettingView()],
    )

    # Run navigation
    nav.run()


if __name__ == "__main__":
    main()
