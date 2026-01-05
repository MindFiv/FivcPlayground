__all__ = [
    "create_tooling_task_async",
    "create_briefing_task_async",
    "create_assessing_task_async",
    "create_planning_task_async",
    "TaskAssessment",
    "TaskRequirement",
    "TaskRunPhase",
    "TaskRunStatus",
]

from fivcplayground.agents import (
    create_tooling_agent,
    create_companion_agent,
    create_consultant_agent,
    create_planning_agent,
    AgentConfigRepository,
    AgentBackend,
)
from fivcplayground.models import (
    ModelConfigRepository,
    ModelBackend,
)
from fivcplayground.tasks.types import (
    TaskAssessment,
    TaskRequirement,
    TaskRunPhase,
    TaskRunStatus,
    TaskRunnable,
    TaskSimpleRunnable,
)
from fivcplayground.tools import ToolRetriever


async def create_tooling_task_async(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable:
    """
    Create a tooling task to identify required tools for a query.
    """
    agent_runnable = create_tooling_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
    )
    return TaskSimpleRunnable(
        agent_runnable,
        query="Retrieve the best tools for the following task: \n{query}",
        response_model=TaskRequirement,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


async def create_briefing_task_async(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable:
    agent_runnable = create_companion_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
    )
    return TaskSimpleRunnable(
        agent_runnable,
        query="Summarize the following content and make it brief and short enough, "
        "say less than 10 words, so that it can be set as a title: \n{query}",
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


async def create_assessing_task_async(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable:
    agent_runnable = create_consultant_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
    )
    return TaskSimpleRunnable(
        agent_runnable,
        query="Assess the following query and determine the best approach for handling it. "
        "Provide your assessment in JSON format with these exact fields:\n"
        "- require_planning (bool): Whether a planning agent is required to break down the task. "
        "Set to true for complex tasks that need multiple steps or specialized agents.\n"
        "- reasoning (string): Brief explanation of your assessment\n\n"
        "Query: {query}",
        response_model=TaskAssessment,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


async def create_planning_task_async(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable:
    """
    Create a planning task to generate a plan for a query.

    Returns a TaskRunnable that generates a plan with specialist agents needed for the task.
    """
    agent_runnable = create_planning_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
    )
    return TaskSimpleRunnable(
        agent_runnable,
        query="Plan the following query and determine the best approach for handling it. "
        "Provide your plan in JSON format with specialist agents needed for the task.\n\n"
        "Query: {query}",
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )
