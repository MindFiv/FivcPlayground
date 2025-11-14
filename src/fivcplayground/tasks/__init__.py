"""
Task creation and management module.

This module provides high-level functions for creating specialized tasks
that leverage agent capabilities for specific purposes:

Task Creation Functions:
    - create_tooling_task: Identify required tools for a query
    - create_briefing_task: Summarize content into a brief title
    - create_assessing_task: Evaluate query complexity and planning needs
    - create_planning_task: Decompose complex queries into specialist teams

Task Types and Models:
    - TaskAssessment: Assessment result with planning requirement
    - TaskRequirement: Tool requirements for a task
    - TaskTeam: Team plan with specialist agents
    - TaskStatus: Execution status enumeration
    - TaskRuntimeStep: Individual agent execution step

Task Management:
    - TaskMonitor: Tracks agent execution through hooks
    - TaskMonitorManager: Manages multiple tasks with centralized monitoring
    - default_manager: Lazy-initialized default TaskMonitorManager instance

All task creation functions return Runnable instances that can be executed
synchronously via run() or asynchronously via run_async().

Example:
    >>> from fivcplayground.tasks import create_assessing_task
    >>> task = create_assessing_task("Is this complex?")
    >>> result = task.run()  # Returns TaskAssessment
    >>> if result.require_planning:
    ...     plan_task = create_planning_task("Plan this task")
    ...     plan = plan_task.run()  # Returns TaskTeam
"""

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
    "default_manager",
]

from typing import Optional, Any

from fivcplayground import agents
from fivcplayground.tasks.types import (
    TaskAssessment,
    TaskRequirement,
    TaskTeam,
    TaskMonitor,
    TaskRuntimeStep,
    TaskStatus,
    TaskMonitorManager,
)
from fivcplayground.tools import ToolsRetriever
from fivcplayground.utils import (
    Runnable,
    ProxyRunnable,
    LazyValue,
)


def create_tooling_task(
    query: str, tools_retriever: Optional[ToolsRetriever] = None, **kwargs: Any
) -> Runnable:
    """
    Create a tooling task to identify required tools for a query.

    This function creates a specialized task that analyzes a user query and
    determines which tools are needed to complete it. The task uses a tooling
    agent to evaluate the query and return a structured TaskRequirement with
    a list of required tool names.

    The tooling task is useful for:
    - Tool selection and planning
    - Capability assessment
    - Pre-execution tool validation
    - Dynamic tool binding

    Args:
        query: The user query to analyze for tool requirements.
               Example: "Calculate the average of [1, 2, 3, 4, 5]"
        tools_retriever: Optional ToolsRetriever instance to provide available
                        tools to the agent. If provided, the tools will be
                        automatically added to the agent's toolkit.
        **kwargs: Additional keyword arguments passed to create_tooling_agent,
                 such as model, temperature, max_tokens, etc.

    Returns:
        Runnable: A TaskRunnable instance that executes the tooling task.
                 Call .run() or .run_async() to execute and get TaskRequirement.

    Raises:
        ValueError: If query is empty or None.
        Exception: Any exception from create_tooling_agent.

    Example:
        >>> from fivcplayground.tasks import create_tooling_task
        >>> task = create_tooling_task("Calculate 123 * 456")
        >>> result = task.run()  # Returns TaskRequirement
        >>> print(result.tools)  # ['calculator']

    Note:
        The response_model is automatically set to TaskRequirement and passed to
        the underlying agent. The agent's create_agent function handles the
        conversion from LLM output to TaskRequirement model automatically.
        The query is prepended with "Retrieve the best tools for the following task:"
    """
    if "tools" not in kwargs and tools_retriever is not None:
        kwargs["tools"] = [tools_retriever.to_tool()]

    # Extract response_model before passing to agent
    kwargs["response_model"] = TaskRequirement

    # Create tooling agent
    return ProxyRunnable(
        agents.create_tooling_agent(**kwargs),
        query=f"Retrieve the best tools for the following task: \n{query}",
    )


def create_briefing_task(
    query: str, tools_retriever: Optional[ToolsRetriever] = None, **kwargs: Any
) -> Runnable:
    """
    Create a briefing task to summarize content into a concise title.

    This function creates a specialized task that takes content or a query
    and produces a brief, concise summary suitable for use as a title or
    heading. The task uses a consultant agent to analyze and condense the
    information.

    The briefing task is useful for:
    - Generating task titles from descriptions
    - Creating summaries for UI display
    - Condensing long queries into brief labels
    - Content abstraction and summarization

    Args:
        query: The content to summarize. Can be a long description, query,
               or any text that needs to be condensed into a brief title.
               Example: "I need to analyze sales data from Q1 and Q2..."
        tools_retriever: Optional ToolsRetriever instance to provide available
                        tools to the agent. If provided, the tools will be
                        automatically added to the agent's toolkit.
        **kwargs: Additional keyword arguments passed to create_consultant_agent,
                 such as model, temperature, max_tokens, etc.

    Returns:
        Runnable: A TaskRunnable instance that executes the briefing task.
                 Call .run() or .run_async() to execute and get a string summary.

    Raises:
        ValueError: If query is empty or None.
        Exception: Any exception from create_consultant_agent.

    Example:
        >>> from fivcplayground.tasks import create_briefing_task
        >>> task = create_briefing_task(
        ...     "I need to analyze sales data from Q1 and Q2 to identify trends"
        ... )
        >>> result = task.run()  # Returns summary string
        >>> print(result)  # "Q1-Q2 Sales Trend Analysis"

    Note:
        The query is prepended with "Summarize the following content and make it brief,
        so that it can be set as a title:"
        The response is typically a string suitable for use as a title.
    """
    if "tools" not in kwargs and tools_retriever is not None:
        kwargs["tools"] = [tools_retriever.to_tool()]

    return ProxyRunnable(
        agents.create_consultant_agent(**kwargs),
        query=f"Summarize the following content and make it brief and short enough, "
        "say less than 10 words, so that it can be set as a title: \n"
        f"{query}",
    )


def create_assessing_task(
    query: str,
    tools_retriever: Optional[ToolsRetriever] = None,
    **kwargs: Any,
) -> Runnable:
    """
    Create an assessing task to evaluate query complexity and planning needs.

    This function creates a specialized task that analyzes a user query to
    determine its complexity and whether it requires planning (breaking down
    into multiple steps with specialized agents). The task returns a structured
    TaskAssessment with complexity evaluation and reasoning.

    The assessing task is useful for:
    - Query complexity evaluation
    - Planning requirement determination
    - Task routing and orchestration
    - Workflow optimization
    - Capability assessment

    Args:
        query: The user query to assess for complexity and planning needs.
               Example: "Analyze sales trends and create a forecast model"
        tools_retriever: Optional ToolsRetriever instance to provide available
                        tools to the agent. If provided, the tools will be
                        automatically added to the agent's toolkit.
        **kwargs: Additional keyword arguments passed to create_consultant_agent,
                 such as model, temperature, max_tokens, etc.

    Returns:
        Runnable: A TaskRunnable instance that executes the assessing task.
                 Call .run() or .run_async() to execute and get TaskAssessment.

    Raises:
        ValueError: If query is empty or None.
        Exception: Any exception from create_consultant_agent.

    Example:
        >>> from fivcplayground.tasks import create_assessing_task
        >>> task = create_assessing_task("Analyze sales data and create forecast")
        >>> result = task.run()  # Returns TaskAssessment
        >>> print(result.require_planning)  # True
        >>> print(result.reasoning)  # "Complex task requiring data analysis..."

    Note:
        The response_model is automatically set to TaskAssessment and passed to
        the underlying agent. The agent's create_agent function handles the
        conversion from LLM output to TaskAssessment model automatically.
        The assessment includes:
        - require_planning: Boolean indicating if planning is needed
        - reasoning: Explanation of the assessment decision
    """
    if "tools" not in kwargs and tools_retriever is not None:
        kwargs["tools"] = [tools_retriever.to_tool()]

    # Extract response_model before passing to agent
    kwargs["response_model"] = TaskAssessment

    return ProxyRunnable(
        agents.create_consultant_agent(**kwargs),
        query=f"Assess the following query and determine the best approach for handling it. "
        f"Provide your assessment in JSON format with these exact fields:\n"
        f"- require_planning (bool): Whether a planning agent is required to break down the task. "
        f"Set to true for complex tasks that need multiple steps or specialized agents.\n"
        f"- reasoning (string): Brief explanation of your assessment\n\n"
        f"Query: {query}",
    )


def create_planning_task(
    query: str,
    tools_retriever: Optional[ToolsRetriever] = None,
    **kwargs,
) -> Runnable:
    """
    Create a planning task to decompose complex queries into specialist teams.

    This function creates a specialized task that analyzes a complex query and
    creates a plan for handling it by defining a team of specialist agents.
    Each specialist has a name, backstory (system prompt), and required tools.
    The task returns a structured TaskTeam with the planned specialist agents.

    The planning task is useful for:
    - Complex task decomposition
    - Multi-agent team planning
    - Specialist agent orchestration
    - Workflow design and optimization
    - Capability-based agent selection

    Args:
        query: The complex query to plan and decompose into specialist tasks.
               Example: "Analyze market trends, create forecast, and generate report"
        tools_retriever: Optional ToolsRetriever instance to provide available
                        tools to the agent. If provided, the tools will be
                        automatically added to the agent's toolkit.
        **kwargs: Additional keyword arguments passed to create_planning_agent,
                 such as model, temperature, max_tokens, etc.

    Returns:
        Runnable: A TaskRunnable instance that executes the planning task.
                 Call .run() or .run_async() to execute and get TaskTeam.

    Raises:
        ValueError: If query is empty or None.
        Exception: Any exception from create_planning_agent.

    Example:
        >>> from fivcplayground.tasks import create_planning_task
        >>> task = create_planning_task(
        ...     "Analyze sales data, create forecast, and generate report"
        ... )
        >>> result = task.run()  # Returns TaskTeam
        >>> print(len(result.specialists))  # 3
        >>> for specialist in result.specialists:
        ...     print(f"{specialist.name}: {specialist.tools}")

    Note:
        The response_model is automatically set to TaskTeam and passed to
        the underlying agent. The agent's create_agent function handles the
        conversion from LLM output to TaskTeam model automatically.
        The plan includes:
        - specialists: List of specialist agents needed
        - Each specialist has: name, backstory, tools
        The backstory serves as the system prompt for the specialist agent.
    """
    if "tools" not in kwargs and tools_retriever is not None:
        kwargs["tools"] = [tools_retriever.to_tool()]

    # Extract response_model before passing to agent
    kwargs["response_model"] = TaskTeam

    return ProxyRunnable(
        agents.create_planning_agent(**kwargs),
        query=f"Plan the following query and determine the best approach for handling it. "
        f"Provide your plan in JSON format with these exact fields:\n"
        f"- specialists (array): List of specialist agents needed for the task\n"
        f"  Each specialist should have:\n"
        f"  - name (string): Name of the agent\n"
        f"  - backstory (string): System prompt/backstory for the agent\n"
        f"  - tools (array): List of tool names the agent needs\n\n"
        f"Query: {query}",
    )


default_manager = LazyValue(lambda: TaskMonitorManager())
