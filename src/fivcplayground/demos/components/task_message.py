"""
Task Message Component

Renders task execution details with runtime information.

This module provides the TaskMessage component for displaying task information
in the FivcPlayground interface, including task metadata, execution steps,
and real-time progress updates.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from fivcplayground.tasks.types import TaskRun, TaskRunStatus


class TaskMessage:
    """
    Component for rendering task execution details with runtime information.

    This class handles the display of task information in the FivcPlayground interface, including:
    - Task metadata (query, status, timing)
    - Task execution steps with agent details
    - Real-time runtime changes and progress updates
    - Message history for each execution step

    Features:
        - Shows execution steps with status indicators and timing
        - Renders messages exchanged during agent execution
        - Supports both completed and streaming task execution
        - Provides expandable sections for detailed information
        - Color-coded status indicators for quick visual feedback

    Class Variables:
        STATUS_ICONS (dict): Mapping of TaskStatus to emoji indicators
        STATUS_COLORS (dict): Mapping of TaskStatus to color descriptions

    Example:
        >>> runtime = TaskRun(...)
        >>> task_msg = TaskMessage(runtime)
        >>> task_msg.render(st.container())
    """

    # Status indicators with emoji
    STATUS_ICONS = {
        TaskRunStatus.PENDING: "🟡",
        TaskRunStatus.EXECUTING: "🔵",
        TaskRunStatus.COMPLETED: "🟢",
        TaskRunStatus.FAILED: "🔴",
    }

    def __init__(self, runtime: TaskRun):
        """
        Initialize TaskMessage with a TaskRun instance.

        Args:
            runtime: TaskRun instance containing task execution data
        """
        self.runtime = runtime

    def render(self, placeholder: DeltaGenerator):
        """
        Render the task execution details.

        Displays comprehensive task information including:
        - Task metadata (query, status, duration)
        - Execution steps with agent progress
        - Messages and results from each step

        Args:
            placeholder: Streamlit container to render into
        """
        placeholder = placeholder.container()

        # Render task header with status
        self._render_task_header(placeholder)

        # Render execution phases
        if self.runtime.phases:
            self._render_execution_steps(placeholder)

    def _render_task_header(self, placeholder: DeltaGenerator):
        """
        Render task header with query, status, and timing information.

        Args:
            placeholder: Streamlit container to render into
        """
        with placeholder.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            # Task query
            if self.runtime.query:
                col1.markdown(f"**Query:** {self.runtime.query}")

            # Status badge
            status_icon = self.STATUS_ICONS.get(self.runtime.status, "⚪")
            col2.markdown(f"{status_icon} **Status:** {self.runtime.status.value}")

            # Duration
            if self.runtime.duration:
                col3.markdown(f"⏱️ **Duration:** {self.runtime.duration:.2f}s")

    def _render_execution_steps(self, placeholder: DeltaGenerator):
        """
        Render task execution steps with agent details and messages.

        Displays each execution step with agent information, status, timing,
        messages exchanged, and any errors that occurred.

        Args:
            placeholder: Streamlit container to render into
        """
        with placeholder.expander("⚙️ **Execution Steps**", expanded=True):
            for step_id, step in self.runtime.phases.items():
                with st.container():
                    # Step header with agent name and status
                    col1, col2, col3 = st.columns([2, 1, 1])

                    col1.markdown(f"**Agent:** {step.agent_name}")

                    status_icon = self.STATUS_ICONS.get(step.status, "⚪")
                    col2.markdown(f"{status_icon} {step.status.value}")

                    if step.duration:
                        col3.markdown(f"⏱️ {step.duration:.2f}s")

                    # Step details
                    if step.started_at:
                        st.caption(f"Started: {step.started_at.isoformat()}")

                    if step.completed_at:
                        st.caption(f"Completed: {step.completed_at.isoformat()}")

                    # Messages
                    if step.messages:
                        self._render_step_messages(placeholder, step.messages)

                    # Error information
                    if step.error:
                        st.error(f"Error: {step.error}")

                    st.divider()

    @staticmethod
    def _render_step_messages(placeholder: DeltaGenerator, messages: list):
        """
        Render messages exchanged during a step execution.

        Args:
            placeholder: Streamlit container to render into
            messages: List of Message objects from the step
        """
        with placeholder.expander("💬 Messages", expanded=False):
            for msg in messages:
                # Handle both dict and Message object formats
                if isinstance(msg, dict):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", [])
                else:
                    # Assume it's a Message object with dict-like access
                    role = (
                        msg.get("role", "unknown") if hasattr(msg, "get") else "unknown"
                    )
                    content = msg.get("content", []) if hasattr(msg, "get") else []

                st.markdown(f"**{role}:**")

                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            st.write(block["text"])
                        elif isinstance(block, str):
                            st.write(block)
                else:
                    st.write(content)
