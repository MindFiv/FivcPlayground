__all__ = [
    "create_agent",
    "create_agent_async",
    "create_companion_agent",
    "create_tooling_agent",
    "create_consultant_agent",
    "create_planning_agent",
    "create_research_agent",
    "create_engineering_agent",
    "create_evaluating_agent",
    "AgentRunContent",
    "AgentRunEvent",
    "AgentRunStatus",
    "AgentRunToolCall",
    "AgentRunSession",
    "AgentRunRepository",
    "AgentRunnable",
    "AgentRun",
    "AgentBackend",
    "AgentConfig",
    "AgentConfigRepository",
    "AgentRunSessionSpan",
    "AgentRunToolSpan",
]

from datetime import datetime
from typing import List
from typing_extensions import deprecated

from fivcplayground.agents.types import (
    AgentRun,
    AgentRunContent,
    AgentRunEvent,
    AgentRunStatus,
    AgentRunToolCall,
    AgentRunSession,
    AgentRunnable,
    AgentBackend,
    AgentConfig,
    AgentConfigRepository,
    AgentRunRepository,
)
from fivcplayground.models import (
    ModelConfigRepository,
    ModelBackend,
    create_model_async,
)
from fivcplayground.tools import (
    Tool,
    ToolBundle,
    ToolRetriever,
)


async def create_agent_async(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    agent_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create a standard ReAct agent for task execution."""
    if not agent_backend:
        if raise_exception:
            raise RuntimeError("No agent backend specified")

        return None

    if not agent_config_repository:
        if raise_exception:
            raise RuntimeError("No agent config repository specified")

        return None

    agent_config = await agent_config_repository.get_agent_config_async(agent_config_id)
    if not agent_config:
        if raise_exception:
            raise ValueError(f"Agent config not found: {agent_config_id}")
        return None

    agent_model = await create_model_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        model_config_id=agent_config.model_id,
        raise_exception=raise_exception,
    )
    if not agent_model:
        if raise_exception:
            raise ValueError(f"Model not found: {agent_config.model_id}")
        return None

    return agent_backend.create_agent(
        agent_model,
        agent_config,
    )


@deprecated("Use create_agent_async instead")
def create_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    agent_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create a standard ReAct agent for task execution."""
    import asyncio

    return asyncio.run(
        create_agent_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_backend=agent_backend,
            agent_config_repository=agent_config_repository,
            agent_config_id=agent_config_id,
            raise_exception=raise_exception,
            **kwargs,
        )
    )


@deprecated("Use create_agent(agent_config_id='companion') instead")
def create_companion_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create a friend agent for chat."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="companion",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='tooling') instead")
def create_tooling_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can retrieve tools."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="tooling",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='consultant') instead")
def create_consultant_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can assess tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="consultant",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='planner') instead")
def create_planning_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can plan tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="planner",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='researcher') instead")
def create_research_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can research tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="researcher",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='engineer') instead")
def create_engineering_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can engineer tools."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="engineer",
        **kwargs,
    )


@deprecated("Use create_agent(agent_config_id='evaluator') instead")
def create_evaluating_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can evaluate performance."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        agent_config_id="evaluator",
        **kwargs,
    )


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


class AgentRunToolSpan:
    """Context manager for setup tool context."""

    def __init__(
        self,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        tool_query: AgentRunContent | None = None,
        **kwargs,  # ignore additional kwargs
    ):
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
            tools = [t for t in tools if t is not None]

        elif self._tool_query and self._tool_query.text:
            tools = await self._tool_retriever.retrieve_tools_async(
                self._tool_query.text
            )

        if not tools:
            tools = await self._tool_retriever.list_tools_async()

        return tools

    async def __aenter__(self) -> List[Tool]:
        """Expand tool bundles into individual tools."""
        tools_expanded = []
        for tool in await self.get_tools_async():
            if isinstance(tool, ToolBundle):
                tool_context = tool.setup()
                tools_expanded.extend(await tool_context.__aenter__())
                self._tool_bundle_contexts.append(tool_context)
            else:
                tools_expanded.append(tool)

        return tools_expanded

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        for tool_context in self._tool_bundle_contexts:
            await tool_context.__aexit__(exc_type, exc_val, exc_tb)
