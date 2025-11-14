from abc import abstractmethod
from typing import Optional, List

from fivcglue.interfaces import IComponent
from fivcplayground.agents.types import (
    AgentsRuntimeMeta,
    AgentsRuntime,
    AgentsRuntimeToolCall,
)


class AgentsRuntimeRepository(IComponent):
    """
    Abstract base class for agent runtime data repositories.

    Defines the interface for persisting and retrieving agent execution data.
    Implementations can use different storage backends (files, databases, etc.).

    The repository manages three levels of data:
        1. Agent metadata (AgentsRuntimeMeta) - Agent configuration and identity
        2. Agent runtimes (AgentsRuntime) - Individual execution instances
        3. Tool calls (AgentsRuntimeToolCall) - Tool invocations within runtimes
    """

    @abstractmethod
    def update_agent(self, agent: AgentsRuntimeMeta) -> None:
        """
        Create or update an agent's metadata.

        Args:
            agent: AgentsRuntimeMeta instance containing agent configuration

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent_id will update the existing agent metadata.
        """
        ...

    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentsRuntimeMeta]:
        """
        Retrieve an agent's metadata by ID.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            AgentsRuntimeMeta instance if found, None otherwise
        """
        ...

    @abstractmethod
    def list_agents(self) -> List[AgentsRuntimeMeta]:
        """
        List all agents in the repository.

        Returns:
            List of AgentsRuntimeMeta instances for all agents.
            Returns empty list if no agents exist.

        Note:
            The order of returned agents is implementation-specific but
            should be consistent across calls.
        """
        ...

    @abstractmethod
    def delete_agent(self, agent_id: str) -> None:
        """
        Delete an agent and all its associated runtimes.

        This is a cascading delete operation that removes:
            - Agent metadata
            - All agent runtimes for this agent
            - All tool calls within those runtimes

        Args:
            agent_id: Unique identifier for the agent to delete

        Note:
            This operation should not raise an error if the agent doesn't exist.
        """
        ...

    @abstractmethod
    def update_agent_runtime(self, agent_id: str, agent_runtime: AgentsRuntime) -> None:
        """
        Create or update an agent runtime's metadata.

        Args:
            agent_id: Agent ID that owns this runtime
            agent_runtime: AgentsRuntime instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent_run_id will update the existing runtime.
            Tool calls are stored separately and not included in this operation.
        """
        ...

    @abstractmethod
    def get_agent_runtime(
        self, agent_id: str, agent_run_id: str
    ) -> Optional[AgentsRuntime]:
        """
        Retrieve an agent runtime by agent ID and run ID.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Unique identifier for the runtime instance

        Returns:
            AgentsRuntime instance if found, None otherwise

        Note:
            Tool calls are loaded separately via list_agent_runtime_tool_calls.
        """
        ...

    @abstractmethod
    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """
        Delete an agent runtime and all its tool calls.

        This is a cascading delete operation that removes:
            - Agent runtime metadata
            - All tool calls within this runtime

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Unique identifier for the runtime to delete

        Note:
            This operation should not raise an error if the runtime doesn't exist.
        """
        ...

    @abstractmethod
    def list_agent_runtimes(self, agent_id: str) -> List[AgentsRuntime]:
        """
        List all agent runtimes for a specific agent.

        Args:
            agent_id: Agent ID to list runtimes for

        Returns:
            List of AgentsRuntime instances for the specified agent.
            Returns empty list if no runtimes exist.

        Note:
            The order of returned runtimes is implementation-specific but
            should be consistent across calls. Chronological ordering by
            agent_run_id is recommended.
        """
        ...

    @abstractmethod
    def get_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call_id: str
    ) -> Optional[AgentsRuntimeToolCall]:
        """
        Retrieve a specific tool call by IDs.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID that contains the tool call
            tool_call_id: Unique identifier for the tool call

        Returns:
            AgentsRuntimeToolCall instance if found, None otherwise
        """
        ...

    @abstractmethod
    def update_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call: AgentsRuntimeToolCall
    ) -> None:
        """
        Create or update a tool call for an agent runtime.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID that contains the tool call
            tool_call: AgentsRuntimeToolCall instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same tool_use_id will update the existing tool call.
        """
        ...

    @abstractmethod
    def list_agent_runtime_tool_calls(
        self, agent_id: str, agent_run_id: str
    ) -> List[AgentsRuntimeToolCall]:
        """
        List all tool calls for an agent runtime.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID to list tool calls for

        Returns:
            List of AgentsRuntimeToolCall instances for the specified runtime.
            Returns empty list if no tool calls exist.

        Note:
            The order of returned tool calls is implementation-specific but
            should be consistent across calls.
        """
        ...
