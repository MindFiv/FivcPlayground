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

from fivcplayground.embeddings.types.repositories import FileEmbeddingConfigRepository
from fivcplayground.models.types.repositories import FileModelConfigRepository
from fivcplayground.tools.types.repositories import FileToolConfigRepository
from fivcplayground.tools import (
    create_tool_retriever,
    create_tool_loader,
)
from fivcplayground.agents.types.repositories import (
    FileAgentConfigRepository,
    SqliteAgentRunRepository,
)
from fivcplayground.app.utils import ChatManager
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
    # Page configuration (must be called first)
    st.set_page_config(
        page_title="FivcPlayground - Intelligent Agent Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    agent_run_repository = SqliteAgentRunRepository()
    agent_config_repository = FileAgentConfigRepository()
    model_config_repository = FileModelConfigRepository()
    embedding_config_repository = FileEmbeddingConfigRepository()
    tool_config_repository = FileToolConfigRepository()
    tool_retriever = create_tool_retriever(
        embedding_config_repository=embedding_config_repository,
    )
    tool_loader = create_tool_loader(
        tool_config_repository=tool_config_repository,
        tool_retriever=tool_retriever,
    )
    tool_loader.load()

    chat_manager = ChatManager(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_run_repository=agent_run_repository,
        tool_retriever=tool_retriever,
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
        [GeneralSettingView(), MCPSettingView(tool_config_repository)],
    )

    # Run navigation
    nav.run()


if __name__ == "__main__":
    main()
