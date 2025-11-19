from abc import abstractmethod
from typing import Any, List

from fivcglue import IComponent
from pydantic import BaseModel, Field

from fivcplayground.interfaces.runnables import (
    IRunnableCallback,
    IRunnableSession,
    IRunnable,
)


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    model: str = Field(description="Model name")
    description: str = Field(description="Description of the agent")
    system_prompt: str = Field(description="System prompt for the agent")


class IAgent(IComponent):
    """Interface for agent."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Id of the agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the agent."""

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Configuration of the agent."""

    @abstractmethod
    def get_runnable(
        self,
        query: str,
        callback: IRunnableCallback | None = None,
        session: IRunnableSession | None = None,
        **kwargs: Any,
    ) -> IRunnable:
        """
        Get the runnable for the agent.
        """


class IAgentProvider(IComponent):
    """Interface for agent creation."""

    @abstractmethod
    def list_agents(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> List[IAgent]:
        """list agents instance."""

    @abstractmethod
    def get_agent(
        self,
        name: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> IAgent | None:
        """get agent instance."""
