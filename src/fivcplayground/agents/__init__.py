__all__ = [
    "create_agent_async",
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
    "AgentRunSkillSpan",
    "BoundedAgentRunnable",
    "ParameterizedAgentRunnable",
]

from fivcplayground.models import (
    ModelBackend,
    ModelConfigRepository,
    create_model_async,
)

from .types import (
    AgentBackend,
    AgentConfig,
    AgentConfigRepository,
    AgentRun,
    AgentRunContent,
    AgentRunEvent,
    AgentRunnable,
    AgentRunRepository,
    AgentRunSession,
    AgentRunSessionSpan,
    AgentRunStatus,
    AgentRunToolCall,
    AgentRunToolSpan,
    AgentRunSkillSpan,
    BoundedAgentRunnable,
    ParameterizedAgentRunnable,
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

    return await agent_backend.create_agent_async(
        model_backend,
        model_config_repository,
        agent_config,
    )
