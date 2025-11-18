__all__ = [
    "create_default_agent",
    "create_companion_agent",
    "create_tooling_agent",
    "create_consultant_agent",
    "create_planning_agent",
    "create_research_agent",
    "create_engineering_agent",
    "create_evaluating_agent",
    "default_retriever",
    "default_agent",
    "BaseAgentsCreator",
    "AgentsRetriever",
]

from typing import cast, List
from uuid import uuid4

from fivcplayground import (
    tools,
    utils,
)
from fivcplayground.models import (
    create_default_model,
    create_chat_model,
    create_reasoning_model,
)
from fivcplayground.agents.types import (
    agents_creator,
    AgentsRunnable,
    AgentsRetriever,
    BaseAgentsCreator,
)


@agents_creator("Generic")
def create_default_agent(**kwargs) -> AgentsRunnable:
    """Create a standard ReAct agent for task execution."""

    # Set default role if not provided
    # Support both 'name' and 'agent_name' for backward compatibility
    if "agent_name" not in kwargs:
        kwargs["agent_name"] = kwargs.pop("name", "Generic")

    if "agent_id" not in kwargs:
        kwargs["agent_id"] = str(uuid4())

    if "tools" not in kwargs:
        kwargs["tools"] = tools.default_retriever.get_all()

    if "model" not in kwargs:
        kwargs["model"] = create_default_model()

    return AgentsRunnable(**kwargs)


@agents_creator("Companion")
def create_companion_agent(*args, **kwargs) -> AgentsRunnable:
    """Create a friend agent for chat."""
    kwargs["agent_name"] = "Companion"
    kwargs.setdefault(
        "system_prompt", "You are a companion, or even a close friend of the user. "
    )
    if "model" not in kwargs:
        kwargs["model"] = create_chat_model()

    if "tools" not in kwargs:
        kwargs["tools"] = tools.default_retriever.get_all()

    return create_default_agent(*args, **kwargs)


@agents_creator("Tooling")
def create_tooling_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can retrieve tools."""
    kwargs["agent_name"] = "Tooling"
    kwargs.setdefault(
        "system_prompt",
        "You are a tool retrieval specialist with deep expertise "
        "in identifying the most appropriate tools for a given task. "
        "Skilled at quickly assessing task requirements, "
        "analyzing available toolsets, and "
        "selecting the best tools for the job.",
    )

    if "model" not in kwargs:
        kwargs["model"] = create_reasoning_model()

    return create_default_agent(*args, **kwargs)


@agents_creator(name="Consultant")
def create_consultant_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can assess tasks."""
    kwargs["agent_name"] = "Consultant"
    kwargs.setdefault(
        "system_prompt",
        """
        You are a task assessment specialist with deep expertise in
        determining the best approach for handling a given task.
        Skilled at quickly assessing task requirements, identifying
        the optimal tools and resources needed, or given an answer if
        the task can be handled directly.
        """,
    )
    if "model" not in kwargs:
        kwargs["model"] = create_reasoning_model()

    return create_default_agent(*args, **kwargs)


@agents_creator(name="Planner")
def create_planning_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can plan tasks."""
    kwargs["agent_name"] = "Planner"
    kwargs.setdefault(
        "system_prompt",
        "You are a task planning specialist with deep expertise "
        "in breaking down complex tasks into manageable components. "
        "Skilled at identifying the optimal crew composition, "
        "task prioritization, and workflow orchestration. "
        "Your goal is to create a plan for executing the task "
        "that is both efficient and effective.",
    )
    return create_default_agent(*args, **kwargs)


@agents_creator(name="Researcher")
def create_research_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can research tasks."""
    kwargs["agent_name"] = "Researcher"
    kwargs.setdefault(
        "system_prompt",
        "You are a pattern recognition specialist and domain analysis expert "
        "with deep expertise in workflow optimization. "
        "Skilled at identifying recurring task sequences, "
        "analyzing execution patterns across different domains, "
        "and extracting actionable insights from complex data flows. "
        "Experienced in comprehensive logging analysis and "
        "workflow pattern summarization to "
        "drive continuous system improvement.",
    )
    return create_default_agent(*args, **kwargs)


@agents_creator(name="Engineer")
def create_engineering_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can engineer tools."""
    kwargs["agent_name"] = "Engineer"
    kwargs.setdefault(
        "system_prompt",
        "You are a tool development specialist and code generation expert "
        "with extensive experience in creating composite tools from "
        "existing components. "
        "Skilled at autonomous tool creation, "
        "combining multiple functionalities into cohesive solutions, "
        "and implementing self-improving systems based on usage patterns. "
        "Expert in maintaining toolset ecosystems and "
        "optimizing tool performance for maximum efficiency.",
    )
    return create_default_agent(*args, **kwargs)


@agents_creator(name="Evaluator")
def create_evaluating_agent(*args, **kwargs) -> AgentsRunnable:
    """Create an agent that can evaluate performance."""
    kwargs["agent_name"] = "Evaluator"
    kwargs.setdefault(
        "system_prompt",
        "You are a performance assessment specialist and "
        "quality assurance expert with "
        "deep expertise in automated evaluation systems. "
        "Skilled at monitoring multi-agent workflows, "
        "identifying optimization opportunities, "
        "and implementing human-in-the-loop validation processes. "
        "Expert in performance tracking, "
        "tool effectiveness validation, "
        "and continuous monitoring for decision pattern recognition to "
        "drive system-wide improvements.",
    )
    return create_default_agent(*args, **kwargs)


def _load_retriever() -> AgentsRetriever:
    retriever = AgentsRetriever()
    retriever.add_batch(
        cast(
            List[BaseAgentsCreator],
            [
                create_default_agent,
                create_companion_agent,
                create_tooling_agent,
                create_consultant_agent,
                create_planning_agent,
                create_research_agent,
                create_engineering_agent,
                create_evaluating_agent,
            ],
        )
    )
    return retriever


default_retriever = utils.LazyValue(_load_retriever)
default_agent = utils.LazyValue(lambda: create_companion_agent())
