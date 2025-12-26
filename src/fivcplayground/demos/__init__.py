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

from fivcplayground.backends.chroma import ChromaEmbeddingBackend
from fivcplayground.backends.strands import (
    StrandsAgentBackend,
    StrandsModelBackend,
    StrandsToolBackend,
)
from fivcplayground.embeddings.types.repositories import FileEmbeddingConfigRepository
from fivcplayground.models.types.repositories import FileModelConfigRepository
from fivcplayground.tools.types.repositories import FileToolConfigRepository
from fivcplayground.tools import create_tool_retriever
from fivcplayground.agents.types.repositories import (
    FileAgentConfigRepository,
    FileAgentRunRepository,
)
from fivcplayground.demos.utils import ChatManager
from fivcplayground.demos.views import (
    ViewNavigation,
    ChatView,
    TaskView,
)

# Apply nest_asyncio to allow nested event loops in Streamlit context
nest_asyncio.apply()

agent_backend = StrandsAgentBackend()
agent_run_repository = FileAgentRunRepository()
agent_config_repository = FileAgentConfigRepository()

model_backend = StrandsModelBackend()
model_config_repository = FileModelConfigRepository()

embedding_backend = ChromaEmbeddingBackend()
embedding_config_repository = FileEmbeddingConfigRepository()

tool_backend = StrandsToolBackend()
tool_config_repository = FileToolConfigRepository()


def main():
    """Main Streamlit application entry point with custom ViewNavigation"""
    # Initialize repositories and tool retriever
    tool_retriever = create_tool_retriever(
        tool_backend=tool_backend,
        tool_config_repository=tool_config_repository,
        embedding_backend=embedding_backend,
        embedding_config_repository=embedding_config_repository,
    )
    # tool_retriever.index_tools()

    # Page configuration (must be called first)
    st.set_page_config(
        page_title="FivcPlayground - Intelligent Agent Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    chat_manager = ChatManager(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_run_repository=agent_run_repository,
        tool_retriever=tool_retriever,
    )

    # Create navigation instance
    nav = ViewNavigation()

    # Build chat views dynamically on each run to include newly created chats
    # This ensures that when a new chat is created and saved, it appears in the list
    # after the app reruns
    chat_pages = [ChatView(chat_manager.add_chat())]
    chat_pages.extend([ChatView(chat) for chat in chat_manager.list_chats()])

    # Add sections to navigation
    nav.add_section("Chats", chat_pages)
    nav.add_section(
        "Tasks",
        [TaskView()],
    )

    # Run navigation
    nav.run()


if __name__ == "__main__":
    main()
