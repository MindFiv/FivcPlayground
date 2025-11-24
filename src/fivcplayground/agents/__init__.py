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
from fivcplayground.agents.types.repositories import (
    AgentConfigRepository,
    AgentRunRepository,
)
from fivcplayground.models import (
    ModelConfigRepository,
    create_model,
)
from fivcplayground.agents.types import (
    AgentRunnable,
)


def create_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    agent_config_id: str = "default",
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create a standard ReAct agent for task execution."""
    if not agent_config_repository:
        from fivcplayground.agents.types.repositories.files import (
            FileAgentConfigRepository,
        )

        agent_config_repository = FileAgentConfigRepository()

    agent_config = agent_config_repository.get_agent_config(agent_config_id)
    if not agent_config:
        raise ValueError(f"Agent config not found: {agent_config_id}")

    model = create_model(model_config_repository, agent_config.model_id)
    if not model:
        raise ValueError(f"Model not found: {agent_config.model_id}")

    return AgentRunnable(
        model=model,
        id=agent_config.id,
        description=agent_config.description,
        system_prompt=agent_config.system_prompt,
    )


def create_companion_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create a friend agent for chat."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="companion",
    )


def create_tooling_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can retrieve tools."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="tooling",
    )


def create_consultant_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can assess tasks."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="consultant",
    )


def create_planning_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can plan tasks."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="planner",
    )


def create_research_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can research tasks."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="researcher",
    )


def create_engineering_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can engineer tools."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="engineer",
    )


def create_evaluating_agent(
    model_config_repository: ModelConfigRepository | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    """Create an agent that can evaluate performance."""
    return create_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
        agent_config_id="evaluator",
    )
