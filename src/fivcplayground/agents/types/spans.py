import json
from datetime import datetime
from typing import List

from fivcplayground.tools import (
    ToolRetriever,
    Tool,
    ToolBundle,
)
from .base import (
    AgentRunToolSet,
    AgentRunSession,
    AgentRunContent,
    AgentRunnable,
    AgentRun,
)
from .repositories import AgentRunRepository


class AgentRunToolSpan:
    """Context manager for setup tool context."""

    def __init__(
        self,
        tool_verifier: AgentRunnable | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        tool_query: AgentRunContent | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        self._tool_verifier = tool_verifier
        self._tool_retriever = tool_retriever
        self._tool_ids = tool_ids
        self._tool_query = tool_query
        self._tool_bundle_contexts = []

    async def get_tools_async(self) -> List[Tool]:
        """Get tools from tool retriever."""

        tools = []
        if not self._tool_retriever:
            return tools

        if self._tool_ids:
            tools = [
                await self._tool_retriever.get_tool_async(name)
                for name in self._tool_ids
            ]

        elif self._tool_query:
            tools = await self._tool_retriever.retrieve_tools_async(
                self._tool_query.text
            )
            if self._tool_verifier:
                toolbox = await self._tool_verifier.run_async(
                    query=self._tool_query,
                    query_params={
                        "tools": json.dumps(
                            [
                                {"name": t.name, "description": t.description}
                                for t in tools
                            ]
                        )
                    },
                    tool_retriever=self._tool_retriever,
                    tool_ids=["tool_retriever"],
                    response_model=AgentRunToolSet,
                )
                tools = [
                    await self._tool_retriever.get_tool_async(name)
                    for name in toolbox.tool_ids
                ]
        else:
            # No tool_ids or tool_query specified, use list_tools_async to get all available tools
            tools = await self._tool_retriever.list_tools_async()

        tools = [t for t in tools if t is not None]

        if not tools:
            tools = [self._tool_retriever.to_tool(dummy=True)]

        return tools

    async def __aenter__(self) -> List[Tool]:
        """Expand tool bundles into individual tools."""
        tools_expanded = []
        for tool in await self.get_tools_async():
            if isinstance(tool, ToolBundle):
                tool_context = tool.setup()
                try:
                    tools_expanded.extend(await tool_context.__aenter__())
                    self._tool_bundle_contexts.append(tool_context)
                except Exception as e:
                    print(f"Failed to setup tool bundle {tool.name}: {e}")
            else:
                tools_expanded.append(tool)

        return tools_expanded

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        for tool_context in self._tool_bundle_contexts:
            await tool_context.__aexit__(exc_type, exc_val, exc_tb)


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
