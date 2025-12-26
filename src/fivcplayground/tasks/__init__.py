__all__ = [
    "create_tooling_task",
    "create_briefing_task",
    "create_assessing_task",
    "create_planning_task",
    "TaskAssessment",
    "TaskRequirement",
    "TaskTeam",
    "TaskRunStage",
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
    TaskTeam,
    TaskRunStage,
    TaskRunStatus,
    TaskSimpleRunnable,
)
from fivcplayground.tools import ToolRetriever
from fivcplayground.agents import AgentRunnable


def create_tooling_task(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
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


def create_briefing_task(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
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


def create_assessing_task(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
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


def create_planning_task(
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> AgentRunnable:
    agent_runnable = create_planning_agent(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
    )
    return TaskSimpleRunnable(
        agent_runnable,
        query="Plan the following query and determine the best approach for handling it. "
        "Provide your plan in JSON format with these exact fields:\n"
        "- specialists (array): List of specialist agents needed for the task\n"
        "  Each specialist should have:\n"
        "  - name (string): Name of the agent\n"
        "  - backstory (string): System prompt/backstory for the agent\n"
        "  - tools (array): List of tool names the agent needs\n\n"
        "Query: {query}",
        response_model=TaskTeam,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )
