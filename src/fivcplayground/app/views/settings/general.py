"""
General Settings Page

Provides general application configuration and settings.

This module implements the general settings view for the FivcPlayground web interface,
allowing users to configure application-wide settings. The view handles:
- Model configuration options
- Chat configuration settings
- Task management toggles
- Application preferences
"""

import streamlit as st

from fivcplayground.app.views.base import ViewBase, ViewNavigation


class GeneralSettingView(ViewBase):
    """General Settings view

    Manages application-wide settings and configuration options.
    Provides interfaces for configuring model, chat, and task settings.
    """

    def __init__(self):
        super().__init__("General Setting", "⚙️")

    @property
    def id(self) -> str:
        """Unique identifier for this view."""
        return "general_setting"

    def render(self, nav: "ViewNavigation"):
        """Render general settings page.

        Args:
            nav (ViewNavigation): Navigation instance for page management.
        """
        st.title(self.display_title)

        st.subheader("🤖 Model Configuration")

        # col1, col2 = st.columns(2)
        # with col1:
        #     _ = st.selectbox("Provider", ["OpenAI", "Ollama", "LiteLLM"], index=0)
        #
        # with col2:
        #     _ = st.text_input("Model", "gpt-4")

        st.divider()

        st.subheader("💬 Chat Configuration")

        def _on_change_enable_tasks(enabled: bool):
            """Callback for enabling/disabling tasks.

            Args:
                enabled (bool): Whether tasks should be enabled.
            """
            # TODO: Implement task persistence through proper Config API
            pass

        # Use default value for enable_tasks toggle
        enable_tasks = False
        _ = st.toggle(
            "Enable Tasks",
            enable_tasks,
            on_change=lambda: _on_change_enable_tasks(not enable_tasks),
        )

        # col1, col2 = st.columns(2)
        # with col1:
        #     if st.button("🗑️ 清理旧通知", use_container_width=True):
        #         st.success("已清理 7 天前的通知")
        #
        # with col2:
        #     if st.button("🔄 重置会话", use_container_width=True, type="secondary"):
        #         chat_session = st.session_state.chat_session
        #         chat_session.cleanup()
        #         st.success("会话已重置")
        #         st.rerun()

        st.divider()

        # Save settings
        if st.button("💾 Save", type="primary", use_container_width=False):
            # Save to session_state

            st.success("✅ Saved！")
