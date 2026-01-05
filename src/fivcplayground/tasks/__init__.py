__all__ = [
    "create_tooling_task_async",
    "create_briefing_task_async",
    "create_assessing_task_async",
    "create_planning_task_async",
    "TaskAssessment",
    "TaskRequirement",
    "TaskPlan",
    "TaskPlanRepository",
    "TaskRunPhase",
    "TaskRunStatus",
    "TaskRunnable",
    "TaskRun",
    "TaskRunRepository",
    "TaskBackend",
]

from pydantic import BaseModel

from fivcplayground.agents import (
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
    TaskPlanAgent,
    TaskPlan,
    TaskPlanRepository,
    TaskRunPhase,
    TaskRunStatus,
    TaskRunnable,
    TaskRun,
    TaskRunRepository,
    TaskBackend,
)
from fivcplayground.tools import ToolRetriever


async def create_task_async(
    task_backend: TaskBackend,
    task_plan_repository: TaskPlanRepository | None = None,
    task_plan_id: str = "default",
    task_response_model: BaseModel | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a task instance from a TaskPlan."""
    if not task_backend:
        if raise_exception:
            raise RuntimeError("No task backend specified")
        return None

    if not task_plan_repository:
        if raise_exception:
            raise RuntimeError("No task plan repository specified")
        return None

    task_plan = await task_plan_repository.get_task_plan_async(task_plan_id)
    if not task_plan:
        if raise_exception:
            raise ValueError(f"Task plan not found: {task_plan_id}")
        return None

    return await task_backend.create_task_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        task_plan=task_plan,
        task_response_model=task_response_model,
        tool_retriever=tool_retriever,
        **kwargs,
    )


async def create_tooling_task_async(
    task_backend: TaskBackend | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a tooling task to identify required tools for a query."""
    if not task_backend:
        if raise_exception:
            raise RuntimeError("No task backend specified")
        return None

    task_plan = TaskPlan(
        id="tooling",
        description="Tooling task to identify required tools for a query",
        agents=[
            TaskPlanAgent(
                id="tooling",
                model_id="default",
                description="Identifies required tools for a query",
                tool_ids=["tool_retriever"],
                system_prompt="You are a tool retrieval specialist with deep expertise in identifying the most appropriate tools for a given task. Skilled at quickly assessing task requirements, analyzing available toolsets, and selecting the best tools for the job.",
            )
        ],
    )
    return await task_backend.create_task_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        task_plan=task_plan,
        task_query_template="Identify the required tools for the following query: {query}",
        task_response_model=TaskRequirement,
        tool_retriever=tool_retriever,
        **kwargs,
    )


async def create_briefing_task_async(
    task_backend: TaskBackend | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a briefing task to generate a brief summary of a query."""
    if not task_backend:
        if raise_exception:
            raise RuntimeError("No task backend specified")
        return None

    task_plan = TaskPlan(
        id="briefing",
        description="Briefing task to generate a brief summary of a query",
        agents=[
            TaskPlanAgent(
                id="briefing",
                model_id="default",
                description="Generates a brief summary of a query",
                tool_ids=[],  # no tools needed
                system_prompt="You are a briefing specialist with deep expertise in generating brief summaries of queries. Skilled at quickly assessing task and generating a brief summary of the task query.",
            )
        ],
    )
    return await task_backend.create_task_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        task_plan=task_plan,
        task_query_template="Briefly summarize the following query: {query}",
        tool_retriever=tool_retriever,
        **kwargs,
    )


async def create_assessing_task_async(
    task_backend: TaskBackend | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create an assessment task to determine the best approach for a query."""
    if not task_backend:
        if raise_exception:
            raise RuntimeError("No task backend specified")
        return None

    task_plan = TaskPlan(
        id="assessment",
        description="Assessment task to determine the best approach for a query",
        agents=[
            TaskPlanAgent(
                id="assessment",
                model_id="default",
                description="Assesses tasks and recommends approaches",
                tool_ids=[],  # no tools needed
                system_prompt="You are a task assessment specialist with deep expertise in determining the best approach for handling a given task. Skilled at quickly assessing task requirements, identifying the optimal tools and resources needed, or given an answer if the task can be handled directly.",
            )
        ],
    )
    return await task_backend.create_task_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        task_plan=task_plan,
        task_response_model=TaskAssessment,
        task_query_template="Assess the following query and determine the best approach for handling it: {query}",
        tool_retriever=tool_retriever,
        **kwargs,
    )


async def create_planning_task_async(
    task_backend: TaskBackend | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    tool_retriever: ToolRetriever | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a planning task to break down a complex query into manageable steps."""
    if not task_backend:
        if raise_exception:
            raise RuntimeError("No task backend specified")
        return None

    task_plan = TaskPlan(
        id="planning",
        description="Planning task to break down a complex query into manageable steps",
        agents=[
            TaskPlanAgent(
                id="planning",
                model_id="default",
                description="Creates execution plans and teams",
                tool_ids=["tool_retriever"],
                system_prompt="You are a planning specialist with deep expertise in breaking down complex tasks into manageable steps and creating execution plans. Skilled at quickly assessing task requirements, identifying the optimal tools and resources needed, and creating a plan for execution.",
            )
        ],
    )
    return await task_backend.create_task_async(
        model_backend=model_backend,
        model_config_repository=model_config_repository,
        agent_backend=agent_backend,
        agent_config_repository=agent_config_repository,
        task_plan=task_plan,
        task_response_model=TaskPlan,
        task_query_template="Plan the following query and determine the best approach for handling it. "
        "Provide your plan in JSON format with specialist agents needed for the task.\n\n"
        "Query: {query}",
        tool_retriever=tool_retriever,
        **kwargs,
    )
