__all__ = [
    "create_tooling_task_async",
    "create_briefing_task_async",
    "create_assessing_task_async",
    "create_planning_task_async",
    "create_planned_task_async",
    "TaskAssessment",
    "TaskPlan",
    "TaskPlanRepository",
    "TaskRunPhase",
    "TaskRunStatus",
    "TaskRunnable",
    "TaskRun",
    "TaskRunRepository",
    "TaskBackend",
]

from fivcplayground.agents import (
    AgentConfig,
    AgentConfigRepository,
    AgentRunToolSet,
    AgentBackend,
    BoundedAgentRunnable,
    ParameterizedAgentRunnable,
)
from fivcplayground.models import (
    ModelConfigRepository,
    ModelBackend,
)

from .types import (
    TaskAssessment,
    TaskPlan,
    TaskPlanRepository,
    TaskRunPhase,
    TaskRunStatus,
    TaskRunnable,
    TaskRun,
    TaskRunRepository,
    TaskBackend,
)


async def create_tooling_task_async(
    agent_backend: AgentBackend | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a tooling task to identify required tools for a query."""
    try:
        if not agent_backend:
            raise RuntimeError("No agent backend specified")

        agent_runnable = await agent_backend.create_agent_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_config=AgentConfig(
                id="tooling",
                model_id="default",
                description="Identifies required tools for a query",
                tool_ids=[],
                # system_prompt="You are a tool retrieval specialist with deep expertise in identifying the most appropriate tools for a given task. Skilled at analyzing available tools, and selecting the best tools for the job.",
            ),
        )
        if not agent_runnable:
            raise RuntimeError("Failed to create agent runnable")

        return ParameterizedAgentRunnable(
            BoundedAgentRunnable(
                agent_runnable,
                # tool_retriever=tool_retriever,
                response_model=AgentRunToolSet,
            ),
            query_format="Identify the most appropriate tool_ids for the query below in the following toolbox rather than registered tools.\n\n\nQuery: {query}\n\nToolbox: {tools}",
        )
    except Exception as e:
        if raise_exception:
            raise e
        return None


async def create_briefing_task_async(
    agent_backend: AgentBackend | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a briefing task to generate a brief summary of a query."""
    try:
        if not agent_backend:
            raise RuntimeError("No agent backend specified")

        agent_runnable = await agent_backend.create_agent_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_config=AgentConfig(
                id="briefing",
                model_id="default",
                description="Generates a brief summary of a query",
                tool_ids=[],  # no tools needed
                system_prompt="You are a briefing specialist with deep expertise in generating brief summaries of queries. Skilled at quickly assessing task and generating a brief summary of the task query.",
            ),
        )
        if not agent_runnable:
            raise RuntimeError("Failed to create agent runnable")

        return ParameterizedAgentRunnable(
            agent_runnable,
            query_format="Briefly summarize the following query to less than 15 words: {query}",
        )
    except Exception as e:
        if raise_exception:
            raise e
        return None


async def create_assessing_task_async(
    agent_backend: AgentBackend | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create an assessment task to determine the best approach for a query."""
    try:
        if not agent_backend:
            raise RuntimeError("No agent backend specified")

        agent_runnable = await agent_backend.create_agent_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_config=AgentConfig(
                id="assessment",
                model_id="default",
                description="Assesses tasks and recommends approaches",
                tool_ids=[],  # no tools needed
                system_prompt="You are a task assessment specialist with deep expertise in determining the best approach for handling a given task. Skilled at quickly assessing task requirements, identifying the optimal tools and resources needed, or given an answer if the task can be handled directly.",
            ),
        )
        if not agent_runnable:
            raise RuntimeError("Failed to create agent runnable")

        return ParameterizedAgentRunnable(
            BoundedAgentRunnable(
                agent_runnable,
                # tool_retriever=tool_retriever,
                response_model=TaskAssessment,
            ),
            query_format="Assess the following query and determine the best approach for handling it: {query}",
        )
    except Exception as e:
        if raise_exception:
            raise e
        return None


async def create_planning_task_async(
    agent_backend: AgentBackend | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """Create a planning task to break down a complex query into manageable steps."""
    try:
        if not agent_backend:
            raise RuntimeError("No agent backend specified")
        agent_runnable = await agent_backend.create_agent_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_config=AgentConfig(
                id="planning",
                model_id="default",
                description="Creates execution plans and teams",
                tool_ids=[],  # no tools needed
                system_prompt="You are a planning specialist with deep expertise in breaking down complex tasks into manageable steps and creating execution plans. Skilled at quickly assessing task requirements, identifying the optimal tools and resources needed, and creating a plan for execution.",
            ),
        )
        if not agent_runnable:
            raise RuntimeError("Failed to create agent runnable")

        return ParameterizedAgentRunnable(
            BoundedAgentRunnable(
                agent_runnable,
                # tool_retriever=tool_retriever,
                response_model=TaskPlan,
            ),
            query_format="Plan the following query and determine the best approach for handling it: {query}",
        )
    except Exception as e:
        if raise_exception:
            raise e
        return None


async def create_planned_task_async(
    task_plan: TaskPlan | None = None,
    agent_backend: AgentBackend | None = None,
    agent_config_repository: AgentConfigRepository | None = None,
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> TaskRunnable | None:
    """
    Create a task instance from a TaskPlan.

    Creates a multi-agent task that executes according to the plan specified
    in the TaskPlan object. The task will coordinate multiple agents to
    accomplish the planned steps.

    Args:
        task_plan: The task plan defining the execution strategy and agents.
                   Required for task creation.
        agent_backend: Backend for creating and managing agents.
        agent_config_repository: Repository for agent configurations.
        model_backend: Backend for model operations.
        model_config_repository: Repository for model configurations.
        tool_retriever: Tool retriever for agent tool access.
        raise_exception: If True, raises exceptions on errors. If False,
                        returns None on error.
        **kwargs: Additional arguments passed to backend implementation.

    Returns:
        TaskRunnable instance if successful, None if task_plan is missing
        and raise_exception is False.

    Raises:
        ValueError: If task_plan is None and raise_exception is True.
        NotImplementedError: Multi-agent tasks are not yet implemented.
    """
    try:
        if not task_plan:
            if raise_exception:
                raise ValueError("Task plan is required")
            return None

        raise NotImplementedError("Multi-agent tasks not implemented yet")
    except Exception as e:
        if raise_exception:
            raise e
        return None
