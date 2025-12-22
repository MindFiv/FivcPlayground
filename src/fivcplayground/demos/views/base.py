"""
ViewNavigation - Custom navigation system for FivcPlayground

A sidebar-based navigation system that replaces st.navigation with more control
and flexibility. Provides better state management and avoids st.navigation limitations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import streamlit as st


class ViewBase(ABC):
    def __init__(
        self,
        title: str,
        icon: str = "",
        is_default: bool = False,
        is_removable: bool = False,
    ):
        self.title = title
        self.icon = icon
        self.is_default = is_default
        self.is_removable = is_removable

    @abstractmethod
    def render(self, nav: "ViewNavigation"): ...

    def on_remove(self, nav: "ViewNavigation"):
        raise NotImplementedError("Cannot remove default view")

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    def display_title(self) -> str:
        """Get formatted display title with icon"""
        if self.icon:
            return f"{self.icon} {self.title}"
        return self.title


class ViewNavigation(object):
    """
    Custom navigation system using sidebar for page selection.

    This component manages both UI rendering and page state persistence.
    State is persisted to run.yml for cross-session consistency.

    The current page is determined by priority:
    1. Page ID from run.yml (via _get_current_page_id())
    2. First page with is_default=True
    3. First page in the first section

    Features:
    - Sidebar-based navigation with sections
    - Support for dynamic page lists (e.g., chat history)
    - Automatic state persistence to run.yml
    - Automatic current page detection from run.yml
    - Abstract base class (ViewBase) for type-safe view implementations

    Example:
        >>> # Define a custom view by inheriting from ViewBase
        >>> class MyView(ViewBase):
        ...     def __init__(self, view_id: str, title: str):
        ...         super().__init__(title=title, icon="📄", is_default=False)
        ...         self._id = view_id
        ...
        ...     @property
        ...     def id(self) -> str:
        ...         return self._id
        ...
        ...     def render(self, nav: ViewNavigation):
        ...         st.title(self.title)
        ...         st.write("View content here")
        >>>
        >>> # Create navigation and add views
        >>> nav = ViewNavigation()
        >>> nav.add_section("Main", [
        ...     MyView("home", "Home"),
        ...     MyView("about", "About"),
        ... ])
        >>> nav.run()  # Automatically shows view from run.yml or default
    """

    def __init__(self):
        """Initialize the navigation system"""
        self.sections: Dict[str, List[ViewBase]] = {}

    def add_section(self, section_name: str, pages: List[ViewBase]):
        """
        Add a navigation section with views.

        Args:
            section_name: Name of the section (e.g., "Chats", "Settings")
            pages: List of ViewBase objects in this section
        """
        self.sections[section_name] = pages

    def add_page(self, section_name: str, page: ViewBase):
        """
        Add a single view to an existing section.

        Args:
            section_name: Name of the section to add to
            page: ViewBase object to add
        """
        if section_name not in self.sections:
            self.sections[section_name] = []
        self.sections[section_name].append(page)

    @staticmethod
    def _get_current_page_id() -> Optional[str]:
        """
        Get the current page ID from persistent storage (run.yml).

        Returns:
            str: The current page ID, or None if not set
        """

        return st.session_state.page_id if "page_id" in st.session_state else None

    @staticmethod
    def _set_current_page_id(page_id: str):
        """
        Set the current page ID in persistent storage (run.yml).

        Args:
            page_id: The page ID to set
        """
        st.session_state.page_id = page_id

    def _get_page(self, page_id: str) -> Optional[ViewBase]:
        """
        Find a page by its page_id across all sections.

        Args:
            page_id: Page id to search for

        Returns:
            ViewBase object if found, None otherwise
        """
        for pages in self.sections.values():
            for page in pages:
                if page.id == page_id:
                    return page
        return None

    def _get_current_page(self) -> Optional[ViewBase]:
        """
        Get the current page to render.

        Priority:
        1. Page matching _get_current_page_id() from run.yml
        2. First page with is_default=True across all sections
        3. First page from the first section

        Returns:
            Current ViewBase object or None if no pages exist
        """
        # Priority 1: Get page from persistent storage (run.yml)
        current_page_id = self._get_current_page_id()
        if current_page_id:
            page = self._get_page(current_page_id)
            if page:
                return page

        # Priority 2: Look for a page with is_default=True
        for pages in self.sections.values():
            for page in pages:
                if page.is_default:
                    return page

        # Priority 3: Return the first page
        for pages in self.sections.values():
            if pages:
                return pages[0]
        return None

    def _render_sidebar(self, current_page: Optional[ViewBase]) -> Optional[ViewBase]:
        """
        Render the sidebar navigation and return clicked page.

        Args:
            current_page: The currently active page (to highlight)

        Returns:
            Clicked ViewBase object or None if no button was clicked
        """
        with st.sidebar:
            # Custom CSS for compact, beautiful navigation
            st.markdown(
                """
                <style>
                /* Reduce sidebar padding */
                [data-testid="stSidebar"] > div:first-child {
                    padding-top: 1rem;
                }

                /* App title styling - compact */
                .nav-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    padding: 0.25rem 0;
                    color: rgb(49, 51, 63);
                }

                /* Dark mode app title */
                @media (prefers-color-scheme: dark) {
                    .nav-title {
                        color: rgb(255, 255, 255);
                    }
                }

                /* Section header styling - compact */
                .nav-section {
                    font-size: 0.7rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: rgb(0, 0, 0);
                    margin-top: 1.25rem;
                    margin-bottom: 0.75rem;
                    padding-left: 0.25rem;
                }

                /* Dark mode section header */
                @media (prefers-color-scheme: dark) {
                    .nav-section {
                        color: rgb(255, 255, 255);
                    }
                }

                /* First section header - more top margin */
                .nav-section:first-of-type {
                    margin-top: 0.5rem;
                }

                /* Compact button styling without border */
                .stButton > button {
                    border-radius: 0.375rem;
                    border: none;
                    padding: 0.25rem 0.625rem;
                    transition: all 0.15s ease;
                    text-align: left !important;
                    font-size: 0.9rem !important;
                    height: auto;
                    min-height: 1.75rem;
                    display: flex;
                    align-items: center;
                    justify-content: flex-start;
                    color: rgba(49, 51, 63, 0.7);
                }

                /* Dark mode button styling */
                @media (prefers-color-scheme: dark) {
                    .stButton > button {
                        color: rgba(255, 255, 255, 0.7);
                    }
                }

                /* Force smaller font size for sidebar buttons */
                [data-testid="stSidebar"] .stButton > button {
                    font-size: 0.9rem !important;
                }

                /* Force smaller font size for button text */
                [data-testid="stSidebar"] .stButton > button > div {
                    font-size: 0.9rem !important;
                }

                /* Button text alignment */
                .stButton > button > div {
                    text-align: left !important;
                    width: 100%;
                    color: inherit;
                }

                /* Secondary button (not selected) */
                .stButton > button[kind="secondary"] {
                    background-color: transparent;
                    color: rgba(49, 51, 63, 0.7);
                }

                .stButton > button[kind="secondary"]:hover {
                    background-color: rgba(151, 166, 195, 0.08);
                    color: rgba(49, 51, 63, 0.85);
                }

                /* Dark mode secondary button */
                @media (prefers-color-scheme: dark) {
                    .stButton > button[kind="secondary"] {
                        color: rgba(255, 255, 255, 0.7);
                    }

                    .stButton > button[kind="secondary"]:hover {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: rgba(255, 255, 255, 0.9);
                    }
                }

                /* Primary button (selected) - use blue instead of red */
                .stButton > button[kind="primary"] {
                    background-color: rgba(28, 131, 225, 0.1);
                    color: rgb(28, 131, 225);
                    font-weight: 500;
                }

                .stButton > button[kind="primary"]:hover {
                    background-color: rgba(28, 131, 225, 0.15);
                }

                /* Minimal spacing between buttons - aggressive override */
                .stButton {
                    margin-bottom: 0 !important;
                    margin-top: 0 !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                    gap: 0 !important;
                }

                /* Remove gap in button container's parent */
                [data-testid="stSidebar"] .stButton {
                    margin: 0 !important;
                    padding: 0 !important;
                }

                /* Remove gap between elements in sidebar */
                [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                    gap: 0.125rem !important;
                }

                /* Remove extra spacing from element container */
                [data-testid="stSidebar"] .element-container {
                    margin: 0 !important;
                    padding: 0 !important;
                }

                /* Expander styling in sidebar */
                [data-testid="stSidebar"] .streamlit-expanderHeader {
                    font-size: 0.75rem !important;
                    font-weight: 600 !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                    color: rgb(0, 0, 0) !important;
                    padding: 0.5rem 0.25rem !important;
                    margin: 0.5rem 0 0.25rem 0 !important;
                    background-color: transparent !important;
                }

                /* Dark mode expander header */
                @media (prefers-color-scheme: dark) {
                    [data-testid="stSidebar"] .streamlit-expanderHeader {
                        color: rgb(255, 255, 255) !important;
                    }
                }

                /* Expander content area */
                [data-testid="stSidebar"] .streamlit-expanderContent {
                    padding: 0 !important;
                    margin: 0 !important;
                    border: none !important;
                }

                /* Expander arrow */
                [data-testid="stSidebar"] .streamlit-expanderHeader svg {
                    width: 0.75rem !important;
                    height: 0.75rem !important;
                }


                </style>
                """,
                unsafe_allow_html=True,
            )

            # App title - compact
            st.markdown(
                '<div class="nav-title">🤖 FivcPlayground</div>', unsafe_allow_html=True
            )

            clicked_page = None

            for section_name, pages in self.sections.items():
                if not pages:
                    continue

                # Check if any page in this section is currently selected
                has_current_page = any(
                    current_page and page.id == current_page.id for page in pages
                )

                # Use expander for each section, expanded if it contains current page
                with st.expander(section_name, expanded=has_current_page):
                    # Render pages in this section
                    for page in pages:
                        # Highlight the current page
                        is_current = current_page and page.id == current_page.id
                        button_type = "primary" if is_current else "secondary"

                        # All buttons are now the same - no delete functionality
                        if st.button(
                            page.display_title,
                            key=f"nav_btn_{page.id}",
                            use_container_width=True,
                            type=button_type,
                        ):
                            clicked_page = page

            return clicked_page

    def navigate_to(self, page_id: str | None):
        """
        Navigate to a specific page by its ID.

        Args:
            page_id: The ID of the page to navigate to
        """
        self._set_current_page_id(page_id or "")
        st.rerun()

    def run(self):
        """
        Run the navigation system and render the selected page.

        This method:
        1. Gets the current page (priority: run.yml > ViewBase.is_default > first page)
        2. Renders the sidebar navigation with current page highlighted
        3. If a button was clicked, saves the page ID to run.yml and reruns
        4. Otherwise, calls the current page's render() method
        """
        # Get the current page (from run.yml or default)
        current_page = self._get_current_page()

        # Render sidebar and check if user clicked a button
        clicked_page = self._render_sidebar(current_page)

        # If user clicked a button, save it to run.yml and rerun
        if clicked_page is not None:
            self._set_current_page_id(clicked_page.id)
            st.rerun()

        # No button clicked - render the current page
        if current_page:
            current_page.render(self)
        else:
            st.error("No pages available to display")
