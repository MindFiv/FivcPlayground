from abc import abstractmethod, ABC
from typing import List

from fivcplayground.agents.types.base import (
    AgentConfig,
    AgentRunSession,
    AgentRun,
)


class AgentConfigRepository(ABC):
    """
    Abstract base class for agent configuration data repositories.

    Defines the interface for persisting and retrieving agent configuration data.
    Implementations can use different storage backends (files, databases, etc.).
    """

    @abstractmethod
    def update_agent_config(self, agent_config: AgentConfig) -> None:
        """Create or update an agent configuration."""
        ...

    @abstractmethod
    def get_agent_config(self, agent_id: str) -> AgentConfig | None:
        """Retrieve an agent configuration by ID."""
        ...

    @abstractmethod
    def list_agent_configs(self) -> List[AgentConfig]:
        """List all agent configurations in the repository."""
        ...

    @abstractmethod
    def delete_agent_config(self, agent_id: str) -> None:
        """Delete an agent configuration."""
        ...


class AgentRunRepository(ABC):
    """
    Abstract base class for agent runtime data repositories.

    Defines the interface for persisting and retrieving agent execution data.
    Implementations can use different storage backends (files, databases, etc.).

    The repository manages three levels of data:
        1. Agent metadata (AgentRunSession) - Agent configuration and identity
        2. Agent runtimes (AgentRun) - Individual execution instances
        3. Tool calls (AgentRunToolCall) - Tool invocations within runtimes
    """

    @abstractmethod
    def update_agent_run_session(self, session: AgentRunSession) -> None:
        """
        Create or update an agent's metadata.

        Args:
            session: AgentRunSession instance containing agent configuration

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent_id will update the existing agent metadata.
        """
        ...

    @abstractmethod
    def get_agent_run_session(self, session_id: str) -> AgentRunSession | None:
        """
        Retrieve an agent's metadata by ID.

        Args:
            session_id: Unique identifier for the agent

        Returns:
            AgentRunSession instance if found, None otherwise
        """
        ...

    @abstractmethod
    def list_agent_run_sessions(self) -> List[AgentRunSession]:
        """
        List all agents in the repository.

        Returns:
            List of AgentRunSession instances for all agents.
            Returns empty list if no agents exist.

        Note:
            The order of returned agents is implementation-specific but
            should be consistent across calls.
        """
        ...

    @abstractmethod
    def delete_agent_run_session(self, session_id: str) -> None:
        """
        Delete an agent and all its associated runtimes.

        This is a cascading delete operation that removes:
            - Agent metadata
            - All agent runtimes for this agent
            - All tool calls within those runtimes

        Args:
            session_id: Unique identifier for the agent to delete

        Note:
            This operation should not raise an error if the agent doesn't exist.
        """
        ...

    @abstractmethod
    def update_agent_run(self, session_id: str, agent_run: AgentRun) -> None:
        """
        Create or update an agent runtime's metadata.

        Args:
            session_id: Session ID that owns this runtime
            agent_run: AgentRun instance to persist (with embedded tool_calls)

        Note:
            This operation is idempotent - calling it multiple times with the
            same id will update the existing runtime.
            Tool calls are embedded within the AgentRun object.
        """
        ...

    @abstractmethod
    def get_agent_run(self, session_id: str, run_id: str) -> AgentRun | None:
        """
        Retrieve an agent runtime by session ID and run ID.

        Args:
            session_id: Session ID that owns the runtime
            run_id: Unique identifier for the runtime instance

        Returns:
            AgentRun instance if found (with embedded tool_calls), None otherwise

        Note:
            Tool calls are embedded within the AgentRun object.
        """
        ...

    @abstractmethod
    def delete_agent_run(self, session_id: str, run_id: str) -> None:
        """
        Delete an agent runtime and all its tool calls.

        This is a cascading delete operation that removes:
            - Agent runtime metadata
            - All tool calls within this runtime

        Args:
            session_id: Session ID that owns the runtime
            run_id: Unique identifier for the runtime to delete

        Note:
            This operation should not raise an error if the runtime doesn't exist.
        """
        ...

    @abstractmethod
    def list_agent_runs(self, session_id: str) -> List[AgentRun]:
        """
        List all agent runtimes for a specific session.

        Args:
            session_id: Session ID to list runtimes for

        Returns:
            List of AgentRun instances for the specified session.
            Returns empty list if no runtimes exist.

        Note:
            The order of returned runtimes is implementation-specific but
            should be consistent across calls. Chronological ordering by
            id is recommended.
            Tool calls are embedded within each AgentRun instance.
        """
        ...
