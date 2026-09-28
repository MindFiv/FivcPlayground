from typing import AsyncIterator

from pydantic import BaseModel

from .base import AgentRun, AgentRunEvent, AgentRunnable


class BoundedAgentRunnable(AgentRunnable):
    """Agent runnable that bounds the query."""

    def __init__(
        self,
        runnable: AgentRunnable,
        **kwargs,
    ):
        self._kwargs = kwargs
        self._runnable = runnable

    @property
    def id(self) -> str:
        return self._runnable.id

    @property
    def name(self) -> str:
        return self._runnable.name

    @property
    def description(self) -> str:
        return self._runnable.description

    async def run_async(self, **kwargs) -> BaseModel:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)

    async def stream_async(
        self, **kwargs
    ) -> AsyncIterator[tuple[AgentRunEvent, AgentRun]]:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        async for event, run in self._runnable.stream_async(**kwargs):
            yield event, run


class ParameterizedAgentRunnable(AgentRunnable):
    """Agent runnable that parameterizes the query."""

    def __init__(
        self,
        runnable: AgentRunnable,
        query_format: str,
        **kwargs,
    ):
        self._query_format = query_format
        self._runnable = runnable

    @property
    def id(self) -> str:
        return self._runnable.id

    @property
    def name(self) -> str:
        return self._runnable.name

    @property
    def description(self) -> str:
        return self._runnable.description

    async def run_async(
        self, query: str = "", query_params: dict[str, str] | None = None, **kwargs
    ) -> BaseModel:
        query_params = query_params or {}
        query_params["query"] = query
        kwargs["query"] = self._query_format.format(**query_params)
        return await self._runnable.run_async(**kwargs)

    async def stream_async(
        self,
        query: str = "",
        query_params: dict[str, str] | None = None,
        **kwargs,
    ) -> AsyncIterator[tuple[AgentRunEvent, AgentRun]]:
        query_params = query_params or {}
        query_params["query"] = query
        kwargs["query"] = self._query_format.format(**query_params)
        async for event, run in self._runnable.stream_async(**kwargs):
            yield event, run
