from pydantic import BaseModel

from fivcplayground.tasks.types.base import TaskRunnable


class SimpleTaskRunnable(TaskRunnable):
    """
    Simple task runnable for testing and development.

    This class provides a basic implementation of the Runnable interface
    for testing and development purposes. It does not perform any actual
    task execution, but simply returns a predefined result.
    """

    def __init__(
        self,
        runnable: TaskRunnable,
        query_template: str = "",
        **kwargs,
    ):
        self._query = query_template
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

    def run(self, query: str = "", **kwargs) -> BaseModel:
        kwargs.update(query=self._query.format(query=query))
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return self._runnable.run(**kwargs)

    async def run_async(self, query: str = "", **kwargs) -> BaseModel:
        kwargs.update(query=self._query.format(query=query))
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)
