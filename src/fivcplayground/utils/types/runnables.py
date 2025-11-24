"""
Runnable abstract base class for FivcPlayground utilities.

This module defines the Runnable abstract base class, which specifies the interface
for objects that support both synchronous and asynchronous execution.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Runnable(ABC):
    """
    Abstract base class for runnable objects that support sync and async execution.

    This abstract base class defines the interface for objects that can be executed
    in both synchronous and asynchronous contexts. Subclasses must implement both
    `run()` and `run_async()` methods to support different execution patterns.

    Both methods accept keyword arguments for flexible parameter passing. Subclasses
    may define additional parameters as needed (e.g., `query`, `monitor`, etc.).

    Abstract Properties:
        id: Unique identifier for the runnable
        name: Human-readable name for the runnable

    Abstract Methods:
        run: Execute the runnable synchronously
        run_async: Execute the runnable asynchronously

    Example:
        >>> class MyRunnable(Runnable):
        ...     @property
        ...     def id(self) -> str:
        ...         return "my-runnable"
        ...
        ...     @property
        ...     def name(self) -> str:
        ...         return "MyRunnable"
        ...
        ...     def run(self, **kwargs):
        ...         return "sync result"
        ...
        ...     async def run_async(self, **kwargs):
        ...         return "async result"
        ...
        >>> runnable = MyRunnable()
        >>> result = runnable.run()
        >>> async_result = await runnable.run_async()
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique identifier for the runnable.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the runnable.
        """

    @abstractmethod
    async def run_async(self, **kwargs: Any) -> BaseModel:
        """
        Execute the runnable asynchronously (abstract method).

        Subclasses must implement this method to perform the runnable's
        operation in an async context, allowing for non-blocking I/O
        and concurrent execution.

        Args:
            **kwargs: Keyword arguments to pass to the runnable

        Returns:
            The result of the async execution
        """

    @abstractmethod
    def run(self, **kwargs: Any) -> BaseModel:
        """
        Execute the runnable synchronously (abstract method).

        Subclasses must implement this method to perform the runnable's
        operation in a synchronous context, blocking until completion.

        Args:
            **kwargs: Keyword arguments to pass to the runnable

        Returns:
            The result of the synchronous execution
        """

    def __call__(self, **kwargs: Any) -> BaseModel:
        """
        Execute the runnable synchronously.

        This method provides a convenient interface for invoking the runnable
        using the function call syntax. It simply delegates to the `run()` method.

        Args:
            **kwargs: Keyword arguments to pass to the runnable

        Returns:
            The result of the synchronous execution

        Example:
            >>> result = runnable(query="test")  # Equivalent to runnable.run(query="test")
        """
        return self.run(**kwargs)


class ProxyRunnable(Runnable):
    """
    Proxy runnable that delegates to another runnable.

    This class provides a proxy implementation of the Runnable interface that
    forwards all execution to a wrapped runnable. It can be used to add
    additional behavior or preprocessing before delegating to the underlying
    runnable.
    """

    def __init__(self, runnable: Runnable, **kwargs: Any):
        self._runnable = runnable
        self._kwargs = kwargs

    @property
    def id(self) -> str:
        return self._runnable.id

    @property
    def name(self) -> str:
        return self._runnable.name

    async def run_async(self, **kwargs: Any) -> BaseModel:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)

    def run(self, **kwargs: Any) -> BaseModel:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return self._runnable.run(**kwargs)
