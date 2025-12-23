__all__ = [
    "create_agent",
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
    create_model,
)
from fivcplayground.tools import (
    Tool,
    ToolBundle,
    ToolRetriever,
)


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
    if not agent_backend:
        if raise_exception:
            raise RuntimeError("No agent backend specified")

        return None

    if not agent_config_repository:
        from fivcplayground.agents.types.repositories.files import (
            FileAgentConfigRepository,
        )

        agent_config_repository = FileAgentConfigRepository()

    agent_config = agent_config_repository.get_agent_config(agent_config_id)
    if not agent_config:
        if raise_exception:
            raise ValueError(f"Agent config not found: {agent_config_id}")
        return None

    agent_model = create_model(
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

        agent_session = self._agent_run_repository.get_agent_run_session(
            self._agent_run_session_id
        )
        if not agent_session:
            self._agent_run_repository.update_agent_run_session(
                AgentRunSession(
                    id=self._agent_run_session_id,
                    agent_id=self._agent_id,
                    started_at=datetime.now(),
                )
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # do nothing

    def __call__(self, agent_run: AgentRun, **kwargs):
        if not self._agent_run_repository or not self._agent_run_session_id:
            return

        self._agent_run_repository.update_agent_run(
            self._agent_run_session_id, agent_run
        )


class AgentRunToolSpan:
    """Context manager for setup tool context."""

    @staticmethod
    def _get_tools(
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        tool_query: AgentRunContent | None = None,
    ):
        tools = []
        if not tool_retriever:
            return tools

        if tool_ids:
            tools = [tool_retriever.get_tool(name) for name in tool_ids]
            tools = [t for t in tools if t is not None]

        elif tool_query and tool_query.text:
            tools = tool_retriever.retrieve_tools(tool_query.text)

        if not tools:
            tools = tool_retriever.list_tools()

        return tools

    def __init__(
        self,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        tool_query: AgentRunContent | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        self._tools = self._get_tools(
            tool_retriever=tool_retriever,
            tool_ids=tool_ids,
            tool_query=tool_query,
        )
        self._tool_bundle_contexts = []

    async def __aenter__(self) -> List[Tool]:
        """Expand tool bundles into individual tools."""
        tools_expanded = []
        for tool in self._tools:
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
