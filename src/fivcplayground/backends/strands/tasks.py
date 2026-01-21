from fivcplayground.agents import AgentBackend, AgentConfigRepository
from fivcplayground.models import ModelBackend, ModelConfigRepository
from fivcplayground.tasks import TaskBackend, TaskPlan, TaskRunnable
from fivcplayground.tools import ToolRetriever


class StrandsTaskBackend(TaskBackend):
    """Task backend for strands"""

    async def create_planned_task_async(
        self,
        task_plan: TaskPlan | None = None,
        agent_backend: AgentBackend | None = None,
        agent_config_repository: AgentConfigRepository | None = None,
        model_backend: ModelBackend | None = None,
        model_config_repository: ModelConfigRepository | None = None,
        tool_retriever: ToolRetriever | None = None,
        raise_exception: bool = True,
        **kwargs,  # ignore additional kwargs
    ) -> TaskRunnable | None:
        """Create a task instance from a TaskPlan."""
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
