"""
Chat Page

Provides a simple conversation interface with streaming responses.

This module implements the main chat view for the FivcPlayground web interface,
allowing users to interact with an AI agent through a conversational interface.
The view handles:
- Displaying conversation history
- Accepting user input
- Streaming agent responses in real-time
- Rendering tool calls and thinking processes

The chat uses the Chat utility for state management and the AgentRun
system for tracking execution state and persistence.
"""

import streamlit as st

from fivcplayground.labs.utils import (
    Chat,
    # default_running_config,
)
from fivcplayground.labs.components import ChatMessage
from fivcplayground.agents.types import AgentRun, AgentRunContent

from .base import ViewBase, ViewNavigation


class ChatView(ViewBase):
    def __init__(self, chat: Chat):
        self.chat = chat
        super().__init__(
            title=chat.description if chat.id else "New Chat",
            icon="💬" if chat.id else "➕",
            is_default=not chat.id,
            is_removable=bool(chat.id),
        )

    @property
    def id(self) -> str:
        return self.chat.id

    def on_remove(self, nav: "ViewNavigation"):
        """
        Remove this chat by deleting all its data.

        Args:
            nav: ViewNavigation instance for navigation after deletion
        """
        # Delete the chat data
        self.chat.cleanup()

        # Navigate to the first available chat or new chat
        # The navigation will be handled by the caller via st.rerun()

    def render(self, nav: "ViewNavigation"):
        """
        Render the chat page with conversation history and input.

        Creates a Streamlit chat interface that provides a conversational
        experience with the FivcPlayground agent. The interface includes:

        1. **Chat Utility Initialization**: Creates a Chat instance with the
           default tools retriever. The Chat utility handles agent execution,
           state persistence, and conversation history.

        2. **Page Title**: Displays the chat page title with an emoji icon.

        3. **Conversation History**: Renders all completed agent runtimes from
           previous queries in chronological order. Each runtime includes the
           user query and agent response.

        4. **User Input**: Provides a chat input field for new queries. When
           the user submits a query, it's sent to the agent asynchronously.

        5. **Streaming Responses**: Uses a callback to render streaming text
           and tool calls in real-time as the agent processes the query.

        The chat interface uses AgentRun objects to track both completed
        messages (from history) and streaming responses (during active agent
        execution). All conversation state is automatically persisted to the
        repository.

        Example Flow:
            1. User opens chat page
            2. Previous conversation history is loaded and displayed
            3. User types a query and presses Enter
            4. Query is sent to agent with streaming callback
            5. Agent response streams in real-time
            6. Completed response is added to history
            7. Page is ready for next query

        Note:
            - The Chat instance is created fresh on each page render
            - Conversation history is loaded from the repository
            - The agent_id is auto-generated and persists across renders
            - Streaming updates are rendered via the on_event callback
            - The default tools retriever provides tools based on the query
        """

        # Display chat title if it's an existing chat
        if self.chat.id:
            st.markdown(
                f"""
                <div style="
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-bottom: 1.5rem;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid rgba(49, 51, 63, 0.1);
                ">
                    {self.icon} {self.title}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Display conversation history
        msg_placeholder = st.container()

        runtimes = self.chat.list_history()
        for runtime in runtimes:
            ChatMessage(runtime).render(msg_placeholder)

        logo_placeholder = st.empty()
        if not runtimes:
            # Page title
            # logo_path = os.path.dirname(os.path.dirname(__file__))
            # logo_path = os.path.join(logo_path, "assets", "FivcPlayground.png")
            # _, logo_col, _ = logo_placeholder.columns(3)
            # logo_col.image(logo_path, caption="💬 FivcPlayground At Your Service!")
            logo_placeholder.title("💬 Anything You Want?")

        # Create placeholder for streaming response
        msg_new_placeholder = st.empty()

        # User input field
        if user_query := st.chat_input("Ask me anything..."):
            # Clear logo
            logo_placeholder.empty()

            ChatMessage(
                AgentRun(
                    query=AgentRunContent(text=user_query),
                    # agent_id=self.chat.id,
                )
            ).render(msg_new_placeholder)

            # Execute query with streaming callback
            is_new_chat = self.chat.id is None

            self.chat.ask(
                user_query,
                on_event=lambda rt: ChatMessage(rt).render(msg_new_placeholder),
            )

            if is_new_chat:
                # Set the page_id and rerun to navigate to the new chat
                nav.navigate_to(self.chat.id)

        # Display delete button at the bottom for existing chats
        if self.chat.id:
            st.markdown(
                """
                <style>
                .delete-button-container {
                    display: flex;
                    justify-content: center;
                    margin-top: 2rem;
                    padding-top: 1.5rem;
                    border-top: 1px solid rgba(49, 51, 63, 0.1);
                }

                .delete-button-wrapper {
                    width: 100%;
                    max-width: 300px;
                }
                </style>
                <div class="delete-button-container"></div>
                """,
                unsafe_allow_html=True,
            )

            # Create a container for the delete button with custom styling
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "🗑️  Delete Chat",
                    key=f"delete_chat_{self.chat.id}",
                    help="Delete this chat and all its messages",
                    use_container_width=True,
                ):
                    st.session_state[f"delete_confirm_{self.chat.id}"] = True

            # Show confirmation dialog if needed
            if st.session_state.get(f"delete_confirm_{self.chat.id}"):
                st.markdown("---")
                st.warning(
                    "⚠️ **Are you sure?** This will permanently delete this chat and all its messages. This action cannot be undone."
                )

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button(
                        "🗑️  Confirm Delete",
                        key=f"confirm_delete_{self.chat.id}",
                        use_container_width=True,
                    ):
                        try:
                            self.chat.cleanup()
                            st.success("✅ Chat deleted successfully!")
                            # Clear the confirmation state
                            st.session_state[f"delete_confirm_{self.chat.id}"] = False
                            # Navigate to new chat
                            nav.navigate_to(None)
                        except Exception as e:
                            st.error(f"❌ Error deleting chat: {str(e)}")
                            st.session_state[f"delete_confirm_{self.chat.id}"] = False

                with col3:
                    if st.button(
                        "✕  Cancel",
                        key=f"cancel_delete_{self.chat.id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"delete_confirm_{self.chat.id}"] = False
                        st.rerun()
