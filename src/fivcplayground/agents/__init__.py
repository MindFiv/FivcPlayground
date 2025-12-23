__all__ = [
    "create_agent",
    "create_companion_agent",
    "create_tooling_agent",
    "create_consultant_agent",
    "create_planning_agent",
    "create_research_agent",
    "create_engineering_agent",
    "create_evaluating_agent",
    "AgentRunnable",
    "AgentRun",
    "AgentRunContent",
    "AgentRunEvent",
    "AgentRunStatus",
    "AgentRunToolCall",
    "AgentRunSession",
    "AgentRunRepository",
    "AgentConfigRepository",
]

from fivcplayground.agents.types.base import (
    AgentRun,
    AgentRunContent,
    AgentRunEvent,
    AgentRunStatus,
    AgentRunToolCall,
    AgentRunSession,
)
from fivcplayground.agents.types.repositories.base import (
    AgentConfigRepository,
    AgentRunRepository,
)
from fivcplayground.agents.types.backends import (
    AgentRunnable,
)
from fivcplayground.models import (
    ModelConfigRepository,
    ModelBackend,
    create_model,
)


def create_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    agent_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create a standard ReAct agent for task execution."""
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

    model_wrapper = create_model(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        model_config_id=agent_config.model_id,
        raise_exception=raise_exception,
    )
    if not model_wrapper:
        if raise_exception:
            raise ValueError(f"Model not found: {agent_config.model_id}")
        return None

    # Extract the underlying model from the Model wrapper
    underlying_model = model_wrapper.get_underlying()

    return AgentRunnable(
        model=underlying_model,
        id=agent_config.id,
        description=agent_config.description,
        system_prompt=agent_config.system_prompt,
    )


def create_companion_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create a friend agent for chat."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="companion",
        **kwargs,
    )


def create_tooling_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can retrieve tools."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="tooling",
        **kwargs,
    )


def create_consultant_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can assess tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="consultant",
        **kwargs,
    )


def create_planning_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can plan tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="planner",
        **kwargs,
    )


def create_research_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can research tasks."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="researcher",
        **kwargs,
    )


def create_engineering_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can engineer tools."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="engineer",
        **kwargs,
    )


def create_evaluating_agent(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable | None:
    """Create an agent that can evaluate performance."""
    return create_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="evaluator",
        **kwargs,
    )
