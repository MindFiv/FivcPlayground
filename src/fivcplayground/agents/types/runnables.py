from pydantic import BaseModel

from .base import AgentRunnable


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

    def run(self, **kwargs) -> BaseModel:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return self._runnable.run(**kwargs)

    async def run_async(self, **kwargs) -> BaseModel:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)


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

    def run(
        self, query: str = "", query_params: dict[str, str] | None = None, **kwargs
    ) -> BaseModel:
        query_params = query_params or {}
        query_params["query"] = query
        kwargs["query"] = self._query_format.format(**query_params)
        return self._runnable.run(**kwargs)

    async def run_async(
        self, query: str = "", query_params: dict[str, str] | None = None, **kwargs
    ) -> BaseModel:
        query_params = query_params or {}
        query_params["query"] = query
        kwargs["query"] = self._query_format.format(**query_params)
        return await self._runnable.run_async(**kwargs)
