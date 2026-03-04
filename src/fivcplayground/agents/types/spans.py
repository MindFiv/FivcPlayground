from datetime import datetime
from typing import List

from fivcplayground.tools import (
    Tool,
    ToolBundle,
    ToolRetriever,
)

from .base import (
    AgentRun,
    AgentRunSession,
)
from .repositories import AgentRunRepository


class AgentRunToolSpan:
    """Context manager for dynamic tool setup and lifecycle management.

    Handles tool retrieval, registration, expansion of tool bundles, and cleanup.
    Supports dynamic tool registration via callback pattern for skills.
    """

    def __init__(
        self,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        self._tool_retriever = tool_retriever
        self._tool_ids = tool_ids
        self._tool_contexts = []
        self._tool_loaded = {}
        self._tool_loaded_expanded = {}

    @property
    def tools(self) -> List[Tool]:
        """Get all loaded tools."""
        return list(self._tool_loaded_expanded.values())

    async def get_tools_async(self) -> List[Tool]:
        """Get tools from tool retriever."""
        if not self._tool_retriever:
            return []

        if self._tool_ids:
            tools = [
                await self._tool_retriever.get_tool_async(name)
                for name in self._tool_ids
            ]
        else:
            tools = await self._tool_retriever.list_tools_async()
        tools = [t for t in tools if t is not None]
        if not tools:
            tools = [self._tool_retriever.to_tool(dummy=True)]
        return tools

    async def register_tool_async(self, tool: Tool | str) -> list[Tool]:
        """Register a tool or tool bundle dynamically.

        Args:
            tool: Tool object or tool_id string to register

        Returns:
            List of expanded tools (for bundles, returns individual tools; for regular tools, returns [tool])
            Returns empty list if tool already registered (deduplication) or not found

        Behavior:
            - Handles Tool objects directly
            - Looks up tool_id strings via tool_retriever if provided
            - Expands ToolBundles into individual tools via setup()
            - Deduplicates across _tool_loaded_expanded
            - Stores bundle contexts for cleanup on exit
        """
        if isinstance(tool, str):
            if tool in self._tool_loaded or tool in self._tool_loaded_expanded:
                return []

            if not self._tool_retriever:
                return []

            tool = await self._tool_retriever.get_tool_async(tool)
            if tool is None:
                return []

        elif tool.name in self._tool_loaded or tool.name in self._tool_loaded_expanded:
            return []

        if isinstance(tool, ToolBundle):
            tool_context = tool.setup()
            try:
                tools_expanded = await tool_context.__aenter__()
                tools_expanded = [
                    t
                    for t in tools_expanded
                    if t.name not in self._tool_loaded_expanded
                ]
                self._tool_contexts.append(tool_context)
                self._tool_loaded[tool.name] = tool
                self._tool_loaded_expanded.update({t.name: t for t in tools_expanded})
                return tools_expanded
            except Exception as e:
                print(f"Failed to setup tool bundle {tool.name}: {e}")
                return []
        else:
            self._tool_loaded[tool.name] = tool
            self._tool_loaded_expanded[tool.name] = tool
            return [tool]

    async def __aenter__(self) -> "AgentRunToolSpan":
        """Expand tool bundles into individual tools."""
        for tool in await self.get_tools_async():
            await self.register_tool_async(tool)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        for tool_context in self._tool_contexts:
            await tool_context.__aexit__(exc_type, exc_val, exc_tb)

        self._tool_loaded.clear()
        self._tool_loaded_expanded.clear()
        self._tool_contexts.clear()


class AgentRunSessionSpan:
    """Context manager for tracking agent run sessions."""

    def __init__(
        self,
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        agent_id: str | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        self._agent_run_repository = agent_run_repository
        self._agent_run_session_id = agent_run_session_id
        self._agent_id = agent_id

    async def __aenter__(self) -> "AgentRunSessionSpan":
        if not self._agent_run_repository or not self._agent_run_session_id:
            return self

        agent_session = await self._agent_run_repository.get_agent_run_session_async(
            self._agent_run_session_id
        )
        if not agent_session:
            await self._agent_run_repository.update_agent_run_session_async(
                AgentRunSession(
                    id=self._agent_run_session_id,
                    agent_id=self._agent_id,
                    started_at=datetime.now(),
                )
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # do nothing

    async def __call__(self, agent_run: AgentRun, **kwargs):
        if not self._agent_run_repository or not self._agent_run_session_id:
            return

        await self._agent_run_repository.update_agent_run_async(
            self._agent_run_session_id, agent_run
        )
