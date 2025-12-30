from abc import abstractmethod, ABC
from typing import List
from typing_extensions import deprecated


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

    @deprecated("Use update_agent_config_async instead")
    def update_agent_config(self, agent_config: AgentConfig) -> None:
        """Create or update an agent configuration."""

    @deprecated("Use get_agent_config_async instead")
    def get_agent_config(self, agent_id: str) -> AgentConfig | None:
        """Retrieve an agent configuration by ID."""

    @deprecated("Use list_agent_configs_async instead")
    def list_agent_configs(self) -> List[AgentConfig]:
        """List all agent configurations in the repository."""

    @deprecated("Use delete_agent_config_async instead")
    def delete_agent_config(self, agent_id: str) -> None:
        """Delete an agent configuration."""

    @abstractmethod
    async def update_agent_config_async(self, agent_config: AgentConfig) -> None:
        """Create or update an agent configuration."""

    @abstractmethod
    async def get_agent_config_async(self, agent_id: str) -> AgentConfig | None:
        """Retrieve an agent configuration by ID."""

    @abstractmethod
    async def list_agent_configs_async(self) -> List[AgentConfig]:
        """List all agent configurations in the repository."""

    @abstractmethod
    async def delete_agent_config_async(self, agent_id: str) -> None:
        """Delete an agent configuration."""


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

    @deprecated("Use update_agent_run_session_async instead")
    def update_agent_run_session(self, session: AgentRunSession) -> None:
        """Create or update an agent's metadata."""

    @deprecated("Use get_agent_run_session_async instead")
    def get_agent_run_session(self, session_id: str) -> AgentRunSession | None:
        """Retrieve an agent's metadata by session ID."""

    @deprecated("Use list_agent_run_sessions_async instead")
    def list_agent_run_sessions(self) -> List[AgentRunSession]:
        """List all agents in the repository."""

    @deprecated("Use delete_agent_run_session_async instead")
    def delete_agent_run_session(self, session_id: str) -> None:
        """Delete an agent's metadata and all its runtimes."""

    @deprecated("Use update_agent_run_async instead")
    def update_agent_run(self, session_id: str, agent_run: AgentRun) -> None:
        """Create or update an agent runtime."""

    @deprecated("Use get_agent_run_async instead")
    def get_agent_run(self, session_id: str, run_id: str) -> AgentRun | None:
        """Retrieve an agent runtime by session ID and run ID."""

    @deprecated("Use delete_agent_run_async instead")
    def delete_agent_run(self, session_id: str, run_id: str) -> None:
        """Delete an agent runtime and all its tool calls."""

    @deprecated("Use list_agent_runs_async instead")
    def list_agent_runs(self, session_id: str) -> List[AgentRun]:
        """List all agent runtimes for a specific session."""

    @abstractmethod
    async def update_agent_run_session_async(self, session: AgentRunSession) -> None:
        """Create or update an agent's metadata."""

    @abstractmethod
    async def get_agent_run_session_async(
        self, session_id: str
    ) -> AgentRunSession | None:
        """Retrieve an agent's metadata by session ID."""

    @abstractmethod
    async def list_agent_run_sessions_async(self) -> List[AgentRunSession]:
        """List all agents in the repository."""

    @abstractmethod
    async def delete_agent_run_session_async(self, session_id: str) -> None:
        """Delete an agent's metadata and all its runtimes."""

    @abstractmethod
    async def update_agent_run_async(
        self, session_id: str, agent_run: AgentRun
    ) -> None:
        """Create or update an agent runtime."""

    @abstractmethod
    async def get_agent_run_async(
        self, session_id: str, run_id: str
    ) -> AgentRun | None:
        """Retrieve an agent runtime by session ID and run ID."""

    @abstractmethod
    async def delete_agent_run_async(self, session_id: str, run_id: str) -> None:
        """Delete an agent runtime and all its tool calls."""

    @abstractmethod
    async def list_agent_runs_async(self, session_id: str) -> List[AgentRun]:
        """List all agent runtimes for a specific session."""
