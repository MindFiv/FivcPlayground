from typing import Type

from pydantic import BaseModel

from fivcplayground.agents import AgentBackend, AgentConfigRepository
from fivcplayground.models import ModelBackend, ModelConfigRepository
from fivcplayground.tasks import TaskBackend, TaskPlan, TaskRunnable
from fivcplayground.tasks.types.runnables import SimpleTaskRunnable


class LangchainTaskBackend(TaskBackend):
    """Task backend for langchain"""

    async def create_task_async(
        self,
        model_backend: ModelBackend,
        model_config_repository: ModelConfigRepository,
        agent_backend: AgentBackend,
        agent_config_repository: AgentConfigRepository,
        task_plan: TaskPlan,
        task_response_model: Type[BaseModel] | None = None,
        task_query_template: str | None = None,
        **kwargs,  # ignore additional kwargs
    ) -> TaskRunnable:
        """Create a task instance from a TaskPlan."""
        if len(task_plan.agents) == 0:
            raise RuntimeError("No agents specified for task")

        elif len(task_plan.agents) == 1:
            agent_config = task_plan.agents[0]
            agent_runnable = await agent_backend.create_agent_async(
                model_backend=model_backend,
                model_config_repository=model_config_repository,
                agent_config=agent_config,
            )

            return SimpleTaskRunnable(
                agent_runnable,
                query_template=task_query_template or "",
                response_model=task_response_model,
                **kwargs,
            )

        else:
            raise NotImplementedError("Multi-agent tasks not implemented yet")
