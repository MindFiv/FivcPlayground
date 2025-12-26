"""
Tasks Page

Provides a task management interface with task execution tracking and monitoring.

This module implements the main tasks view for the FivcPlayground web interface,
allowing users to create, monitor, and manage multi-agent tasks. The view handles:
- Displaying task list with status indicators
- Showing task team composition and specialist agents
- Rendering task execution steps with real-time updates
- Tracking runtime changes and agent execution progress

The tasks view uses the TaskManager utility for state management and the TaskRun
system for tracking execution state and persistence.
"""

import streamlit as st

from .base import ViewBase, ViewNavigation


class TaskView(ViewBase):
    """
    View for displaying and managing tasks.

    Provides a task management interface that shows:
    - Task list with status indicators
    - Task team composition (specialists and their tools)
    - Task execution steps with real-time progress
    - Runtime changes and agent execution details
    """

    def __init__(self):
        super().__init__(
            title="Tasks",
            icon="📋",
            is_default=False,
            is_removable=False,
        )

    @property
    def id(self) -> str:
        return "tasks"

    def render(self, nav: "ViewNavigation"):
        """
        Render the tasks page with task list and execution details.

        Creates a Streamlit interface that provides task management capabilities:

        1. **Page Title**: Displays the tasks page title with an emoji icon.

        2. **Task List**: Shows all tasks with status indicators:
           - Status badge (PENDING, EXECUTING, COMPLETED, FAILED)
           - Task query/description
           - Task team information if available
           - Execution timing and duration

        3. **Task Details**: When a task is selected, displays:
           - Full task team composition with specialist agents
           - Each specialist's name, backstory, and required tools
           - Task execution steps with agent details
           - Real-time progress updates for running tasks

        4. **Execution Steps**: For each step in the task:
           - Agent name and status
           - Execution timing (start, end, duration)
           - Messages exchanged during execution
           - Error information if step failed

        The interface automatically updates to show real-time progress
        as tasks execute through the agent swarm.
        """

        # Display page title
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

        # TODO: Integrate with TaskManager to get actual tasks
        # For now, show placeholder
        st.info("📋 Task management interface - Coming soon!")
        st.write("""
        This page will display:
        - Active and completed tasks
        - Task team composition with specialist agents
        - Real-time execution progress
        - Agent step details and messages
        - Task history and results
        """)
