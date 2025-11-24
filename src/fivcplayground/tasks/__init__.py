__all__ = [
    "create_tooling_task",
    "create_briefing_task",
    "create_assessing_task",
    "create_planning_task",
    "TaskAssessment",
    "TaskRequirement",
    "TaskTeam",
    "TaskMonitor",
    "TaskRuntimeStep",
    "TaskStatus",
    "TaskMonitorManager",
]

from fivcplayground.agents import (
    AgentConfigRepository,
    create_tooling_agent,
    create_consultant_agent,
    create_planning_agent,
)
from fivcplayground.models import (
    ModelConfigRepository,
)
from fivcplayground.tasks.types import (
    TaskAssessment,
    TaskRequirement,
    TaskTeam,
    TaskMonitor,
    TaskRuntimeStep,
    TaskStatus,
    TaskMonitorManager,
)
from fivcplayground.tools import ToolRetriever
from fivcplayground.utils import (
    Runnable,
    ProxyRunnable,
)


def create_tooling_task(
    query: str,
    agent_config_repository: AgentConfigRepository | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> Runnable:
    """
    Create a tooling task to identify required tools for a query.
    """

    agent_runnable = create_tooling_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
    )
    return ProxyRunnable(
        agent_runnable,
        query=f"Retrieve the best tools for the following task: \n{query}",
        response_model=TaskRequirement,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


def create_briefing_task(
    query: str,
    agent_config_repository: AgentConfigRepository | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> Runnable:
    agent_runnable = create_consultant_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
    )
    return ProxyRunnable(
        agent_runnable,
        query=f"Summarize the following content and make it brief and short enough, "
        "say less than 10 words, so that it can be set as a title: \n"
        f"{query}",
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


def create_assessing_task(
    query: str,
    agent_config_repository: AgentConfigRepository | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> Runnable:
    agent_runnable = create_consultant_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
    )
    return ProxyRunnable(
        agent_runnable,
        query=f"Assess the following query and determine the best approach for handling it. "
        f"Provide your assessment in JSON format with these exact fields:\n"
        f"- require_planning (bool): Whether a planning agent is required to break down the task. "
        f"Set to true for complex tasks that need multiple steps or specialized agents.\n"
        f"- reasoning (string): Brief explanation of your assessment\n\n"
        f"Query: {query}",
        response_model=TaskAssessment,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )


def create_planning_task(
    query: str,
    agent_config_repository: AgentConfigRepository | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    **kwargs,  # ignore additional kwargs
) -> Runnable:
    agent_runnable = create_planning_agent(
        model_config_repository=model_config_repository,
        agent_config_repository=agent_config_repository,
    )
    return ProxyRunnable(
        agent_runnable,
        query=f"Plan the following query and determine the best approach for handling it. "
        f"Provide your plan in JSON format with these exact fields:\n"
        f"- specialists (array): List of specialist agents needed for the task\n"
        f"  Each specialist should have:\n"
        f"  - name (string): Name of the agent\n"
        f"  - backstory (string): System prompt/backstory for the agent\n"
        f"  - tools (array): List of tool names the agent needs\n\n"
        f"Query: {query}",
        response_model=TaskTeam,
        tool_retriever=tool_retriever,
        tool_ids=["tool_retriever"],
    )
