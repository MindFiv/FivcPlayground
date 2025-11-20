"""
Task Runnable wrapper for agent execution.

This module provides TaskRunnable, a wrapper around agent runnables that
prepends a task-specific query to the execution context.

Key Components:
    - TaskRunnable: Wraps an agent runnable with a task query
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Union, Type, Callable
from uuid import uuid4

from pydantic import BaseModel
from strands.multiagent import Swarm

from fivcplayground.tasks.types import TaskEvent, TaskRuntime
from fivcplayground.tools import ToolRetriever
from fivcplayground.utils import Runnable


class TaskRunnable(Runnable):
    def __init__(
        self,
        task_id: str | None = None,
        task_name: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        response_model: Type[BaseModel] | None = None,
        callback_handler: Callable[[TaskEvent, TaskRuntime], None] | None = None,
        **kwargs,
    ):
        self._id = task_id or str(uuid4())
        self._name = task_name or "Default"
        self._tools_retriever = tool_retriever
        self._response_model = response_model
        self._callback_handler = callback_handler

    @asynccontextmanager
    async def create_swarm_async(self):
        swarm = Swarm()
        return swarm

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def run(self, **kwargs: Any) -> Union[BaseModel, TaskRuntime]:
        return asyncio.run(self.run_async(**kwargs))

    async def run_async(self, **kwargs: Any) -> Union[BaseModel, TaskRuntime]:
        pass
