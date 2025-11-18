"""
File-based agent runtime repository implementation.

This module provides FileAgentsRuntimeRepository, a file-based implementation
of AgentsRuntimeRepository that stores agent data in a hierarchical directory
structure with JSON files.

Storage Structure:
    /<output_dir>/
    └── agent_<agent_id>/
        ├── agent.json               # Agent metadata (AgentsRuntimeMeta)
        └── run_<agent_run_id>/
            ├── run.json             # Agent Runtime metadata (AgentsRuntime)
            └── tool_calls/
                ├── tool_call_<tool_call_id>.json  # Tool call data
                └── tool_call_<tool_call_id>.json

This structure allows for:
    - Multiple runs per agent
    - Easy inspection of agent data
    - Efficient tool-call-by-tool-call updates
    - Simple backup and version control
    - Human-readable JSON format
    - Cascading deletes (deleting an agent removes all its runtimes)

Example:
    >>> from fivcplayground.agents.types.repositories.files import FileAgentsRuntimeRepository
    >>> from fivcplayground.agents.types import AgentsRuntimeMeta, AgentsRuntime
    >>> from fivcplayground.utils import OutputDir
    >>>
    >>> # Create repository
    >>> repo = FileAgentsRuntimeRepository(output_dir=OutputDir("./agents"))
    >>>
    >>> # Store agent metadata
    >>> agent_meta = AgentsRuntimeMeta(
    ...     agent_id="my-agent",
    ...     agent_name="MyAgent",
    ...     system_prompt="You are a helpful assistant"
    ... )
    >>> repo.update_agent(agent_meta)
    >>>
    >>> # Create and store a runtime
    >>> runtime = AgentsRuntime(agent_id="my-agent", agent_name="MyAgent")
    >>> repo.update_agent_runtime("my-agent", runtime)
    >>>
    >>> # List all agents
    >>> agents = repo.list_agents()
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List

from fivcplayground.agents.types import AgentsRuntimeMeta
from fivcplayground.utils import OutputDir

from fivcplayground.agents.types.repositories import (
    AgentsRuntime,
    AgentsRuntimeToolCall,
    AgentsRuntimeRepository,
)


class FileAgentsRuntimeRepository(AgentsRuntimeRepository):
    """
    File-based repository for agent runtime data.

    Stores agent metadata, runtimes, and tool calls in a hierarchical directory
    structure with JSON files. All operations are thread-safe for single-process
    usage.

    Storage structure:
        /<output_dir>/
        └── agent_<agent_id>/
            ├── agent.json               # Agent metadata
            └── run_<agent_run_id>/
                ├── run.json             # Agent Runtime metadata
                └── tool_calls/
                    ├── tool_call_<tool_call_id>.json
                    └── tool_call_<tool_call_id>.json

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root

    Note:
        - All JSON files use UTF-8 encoding with 2-space indentation
        - Corrupted JSON files are logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations create necessary directories automatically
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        """
        Initialize the file-based repository.

        Args:
            output_dir: Optional OutputDir for the repository. If not provided,
                       defaults to OutputDir().subdir("agents")

        Note:
            The base directory is created automatically if it doesn't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("agents")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_agent_dir(self, agent_id: str) -> Path:
        """
        Get the directory path for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to agent directory (e.g., /<base_path>/agent_<agent_id>/)
        """
        return self.base_path / f"agent_{agent_id}"

    def _get_agent_file(self, agent_id: str) -> Path:
        """
        Get the file path for agent metadata.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to agent metadata file (e.g., /<base_path>/agent_<agent_id>/agent.json)
        """
        return self._get_agent_dir(agent_id) / "agent.json"

    def _get_run_dir(self, agent_id: str, agent_run_id: str) -> Path:
        """
        Get the directory path for an agent run.

        Args:
            agent_id: Agent identifier
            agent_run_id: Agent run identifier

        Returns:
            Path to run directory (e.g., /<base_path>/agent_<agent_id>/run_<agent_run_id>/)
        """
        return self._get_agent_dir(agent_id) / f"run_{agent_run_id}"

    def _get_run_file(self, agent_id: str, agent_run_id: str) -> Path:
        """
        Get the file path for agent runtime metadata.

        Args:
            agent_id: Agent identifier
            agent_run_id: Agent run identifier

        Returns:
            Path to runtime file (e.g., /<base_path>/agent_<agent_id>/run_<agent_run_id>/run.json)
        """
        return self._get_run_dir(agent_id, agent_run_id) / "run.json"

    def _get_tool_calls_dir(self, agent_id: str, agent_run_id: str) -> Path:
        """
        Get the directory path for agent tool calls.

        Args:
            agent_id: Agent identifier
            agent_run_id: Agent run identifier

        Returns:
            Path to tool calls directory (e.g., /<base_path>/agent_<agent_id>/run_<agent_run_id>/tool_calls/)
        """
        return self._get_run_dir(agent_id, agent_run_id) / "tool_calls"

    def _get_tool_call_file(
        self, agent_id: str, agent_run_id: str, tool_call_id: str
    ) -> Path:
        """
        Get the file path for a tool call.

        Args:
            agent_id: Agent identifier
            agent_run_id: Agent run identifier
            tool_call_id: Tool call identifier

        Returns:
            Path to tool call file (e.g., /<base_path>/agent_<agent_id>/run_<agent_run_id>/tool_calls/tool_call_<tool_call_id>.json)
        """
        return (
            self._get_tool_calls_dir(agent_id, agent_run_id)
            / f"tool_call_{tool_call_id}.json"
        )

    def update_agent(self, agent: AgentsRuntimeMeta) -> None:
        """
        Create or update an agent's metadata.

        Stores agent configuration including agent_id, agent_name, system_prompt,
        and description in agent.json file. Creates the agent directory if it
        doesn't exist.

        Args:
            agent: AgentsRuntimeMeta instance containing agent configuration

        Example:
            >>> agent_meta = AgentsRuntimeMeta(
            ...     agent_id="my-agent",
            ...     agent_name="MyAgent",
            ...     system_prompt="You are helpful"
            ... )
            >>> repo.update_agent(agent_meta)

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent_id will overwrite the existing metadata.
        """
        agent_dir = self._get_agent_dir(agent.agent_id)
        agent_dir.mkdir(parents=True, exist_ok=True)

        agent_file = self._get_agent_file(agent.agent_id)

        # Serialize agent metadata to JSON
        agent_data = agent.model_dump(mode="json")

        with open(agent_file, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)

    def get_agent(self, agent_id: str) -> Optional[AgentsRuntimeMeta]:
        """
        Retrieve an agent's metadata by ID.

        Reads and deserializes the agent.json file for the specified agent.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            AgentsRuntimeMeta instance if found, None if agent doesn't exist
            or if the agent.json file is corrupted

        Example:
            >>> agent = repo.get_agent("my-agent")
            >>> if agent:
            ...     print(f"Agent: {agent.agent_name}")

        Note:
            Corrupted JSON files are logged to stdout and return None.
        """
        agent_file = self._get_agent_file(agent_id)

        if not agent_file.exists():
            return None

        try:
            with open(agent_file, "r", encoding="utf-8") as f:
                agent_data = json.load(f)

            # Reconstruct AgentsRuntimeMeta from JSON
            return AgentsRuntimeMeta.model_validate(agent_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading agent {agent_id}: {e}")
            return None

    def list_agents(self) -> List[AgentsRuntimeMeta]:
        """
        List all agents in the repository.

        Scans all agent_* directories and loads their metadata. Corrupted
        agent files are skipped.

        Returns:
            List of AgentsRuntimeMeta instances sorted by agent_id.
            Returns empty list if no agents exist or repository is empty.

        Example:
            >>> agents = repo.list_agents()
            >>> for agent in agents:
            ...     print(f"{agent.agent_id}: {agent.agent_name}")

        Note:
            Results are sorted alphabetically by agent_id for consistent ordering.
        """
        agents = []

        if not self.base_path.exists():
            return agents

        # Iterate through all agent directories
        for agent_dir in self.base_path.glob("agent_*"):
            if not agent_dir.is_dir():
                continue

            # Extract agent_id from directory name
            agent_id = agent_dir.name.replace("agent_", "")

            # Load agent metadata
            agent = self.get_agent(agent_id)
            if agent:
                agents.append(agent)

        # Sort by agent_id for consistent ordering
        agents.sort(key=lambda a: a.agent_id)

        return agents

    def delete_agent(self, agent_id: str) -> None:
        """
        Delete an agent and all its associated runtimes.

        This is a cascading delete operation that removes:
            - Agent metadata (agent.json)
            - All agent runtimes for this agent
            - All tool calls within those runtimes

        Args:
            agent_id: Unique identifier for the agent to delete

        Example:
            >>> repo.delete_agent("my-agent")
            >>> # All data for "my-agent" is now deleted

        Note:
            This operation is safe to call on non-existent agents - it will
            not raise an error if the agent doesn't exist.
        """
        agent_dir = self._get_agent_dir(agent_id)

        if agent_dir.exists():
            shutil.rmtree(agent_dir)

    def update_agent_runtime(self, agent_id: str, agent_runtime: AgentsRuntime) -> None:
        """
        Create or update an agent runtime.

        Stores runtime execution metadata including status, timestamps, and
        streaming text. Tool calls are stored separately and not included in
        this operation.

        Args:
            agent_id: Agent ID that owns this runtime
            agent_runtime: AgentsRuntime instance to persist

        Example:
            >>> runtime = AgentsRuntime(
            ...     agent_id="my-agent",
            ...     agent_name="MyAgent",
            ...     status=AgentsStatus.EXECUTING
            ... )
            >>> repo.update_agent_runtime("my-agent", runtime)

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent_run_id will overwrite the existing runtime metadata.
            Creates the run directory if it doesn't exist.
        """
        run_dir = self._get_run_dir(agent_id, str(agent_runtime.agent_run_id))
        run_dir.mkdir(parents=True, exist_ok=True)

        run_file = self._get_run_file(agent_id, str(agent_runtime.agent_run_id))

        # Serialize agent to JSON (exclude tool_calls as they're stored separately)
        agent_data = agent_runtime.model_dump(mode="json", exclude={"tool_calls"})

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)

    def get_agent_runtime(
        self, agent_id: str, agent_run_id: str
    ) -> Optional[AgentsRuntime]:
        """
        Retrieve an agent runtime by agent ID and run ID.

        Reads and deserializes the run.json file for the specified runtime.
        Tool calls are not included and must be loaded separately.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Unique identifier for the runtime instance

        Returns:
            AgentsRuntime instance if found, None if runtime doesn't exist
            or if the run.json file is corrupted

        Example:
            >>> runtime = repo.get_agent_runtime("my-agent", "1234567890.123")
            >>> if runtime:
            ...     print(f"Status: {runtime.status}")

        Note:
            Tool calls are loaded separately via list_agent_runtime_tool_calls.
            Corrupted JSON files are logged to stdout and return None.
        """
        run_file = self._get_run_file(agent_id, agent_run_id)

        if not run_file.exists():
            return None

        try:
            with open(run_file, "r", encoding="utf-8") as f:
                agent_data = json.load(f)

            # Reconstruct AgentsRuntime from JSON
            # Note: tool_calls are loaded separately via list_agent_runtime_tool_calls
            return AgentsRuntime.model_validate(agent_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading agent {agent_id} run {agent_run_id}: {e}")
            return None

    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """
        Delete an agent runtime and all its tool calls.

        This is a cascading delete operation that removes:
            - Runtime metadata (run.json)
            - All tool calls within this runtime

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Unique identifier for the runtime to delete

        Example:
            >>> repo.delete_agent_runtime("my-agent", "1234567890.123")
            >>> # Runtime and all its tool calls are now deleted

        Note:
            This operation is safe to call on non-existent runtimes - it will
            not raise an error if the runtime doesn't exist.
        """
        run_dir = self._get_run_dir(agent_id, agent_run_id)

        if run_dir.exists():
            shutil.rmtree(run_dir)

    def list_agent_runtimes(self, agent_id: str) -> List[AgentsRuntime]:
        """
        List all agent runtimes for a specific agent in chronological order.

        Scans all run_* directories for the specified agent and loads their
        metadata. Corrupted runtime files are skipped.

        Args:
            agent_id: Agent ID to list runtimes for

        Returns:
            List of AgentsRuntime instances sorted by agent_run_id (timestamp)
            in increasing order. Returns empty list if no runtimes exist.

        Example:
            >>> runtimes = repo.list_agent_runtimes("my-agent")
            >>> for runtime in runtimes:
            ...     print(f"{runtime.agent_run_id}: {runtime.status}")

        Note:
            Results are sorted chronologically by agent_run_id (timestamp string)
            for consistent ordering. Earlier runs appear first in the list.
        """
        runtimes = []
        agent_dir = self._get_agent_dir(agent_id)

        if not agent_dir.exists():
            return runtimes

        # Iterate through all run directories for this agent
        for run_dir in agent_dir.glob("run_*"):
            if not run_dir.is_dir():
                continue

            # Extract agent_run_id from directory name
            agent_run_id = run_dir.name.replace("run_", "")

            # Load agent runtime
            runtime = self.get_agent_runtime(agent_id, agent_run_id)
            if runtime:
                runtimes.append(runtime)

        # Sort by agent_run_id (timestamp string) in increasing order
        runtimes.sort(key=lambda r: r.agent_run_id)

        return runtimes

    def get_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call_id: str
    ) -> Optional[AgentsRuntimeToolCall]:
        """
        Retrieve a specific tool call by IDs.

        Reads and deserializes the tool call JSON file for the specified
        tool call within a runtime.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID that contains the tool call
            tool_call_id: Unique identifier for the tool call

        Returns:
            AgentsRuntimeToolCall instance if found, None if tool call doesn't
            exist or if the JSON file is corrupted

        Example:
            >>> tool_call = repo.get_agent_runtime_tool_call(
            ...     "my-agent", "1234567890.123", "tool-call-1"
            ... )
            >>> if tool_call:
            ...     print(f"Tool: {tool_call.tool_name}, Status: {tool_call.status}")

        Note:
            Corrupted JSON files are logged to stdout and return None.
        """
        tool_call_file = self._get_tool_call_file(agent_id, agent_run_id, tool_call_id)

        if not tool_call_file.exists():
            return None

        try:
            with open(tool_call_file, "r", encoding="utf-8") as f:
                tool_call_data = json.load(f)

            # Reconstruct AgentsRuntimeToolCall from JSON
            return AgentsRuntimeToolCall.model_validate(tool_call_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(
                f"Error loading tool call {tool_call_id} for agent {agent_id} run {agent_run_id}: {e}"
            )
            return None

    def update_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call: AgentsRuntimeToolCall
    ) -> None:
        """
        Create or update a tool call for an agent runtime.

        Stores tool call data including tool name, input, result, status, and
        timing information in a separate JSON file.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID that contains the tool call
            tool_call: AgentsRuntimeToolCall instance to persist

        Example:
            >>> tool_call = AgentsRuntimeToolCall(
            ...     tool_use_id="tool-call-1",
            ...     tool_name="calculator",
            ...     tool_input={"expression": "2+2"},
            ...     status="pending"
            ... )
            >>> repo.update_agent_runtime_tool_call(
            ...     "my-agent", "1234567890.123", tool_call
            ... )

        Note:
            This operation is idempotent - calling it multiple times with the
            same tool_use_id will overwrite the existing tool call.
            Creates the tool_calls directory if it doesn't exist.
        """
        tool_calls_dir = self._get_tool_calls_dir(agent_id, agent_run_id)
        tool_calls_dir.mkdir(parents=True, exist_ok=True)

        tool_call_file = self._get_tool_call_file(
            agent_id, agent_run_id, tool_call.tool_use_id
        )

        # Serialize tool call to JSON
        tool_call_data = tool_call.model_dump(mode="json")

        with open(tool_call_file, "w", encoding="utf-8") as f:
            json.dump(tool_call_data, f, indent=2, ensure_ascii=False)

    def list_agent_runtime_tool_calls(
        self, agent_id: str, agent_run_id: str
    ) -> List[AgentsRuntimeToolCall]:
        """
        List all tool calls for an agent runtime.

        Scans all tool_call_*.json files in the runtime's tool_calls directory
        and loads their data. Corrupted tool call files are skipped.

        Args:
            agent_id: Agent ID that owns the runtime
            agent_run_id: Runtime ID to list tool calls for

        Returns:
            List of AgentsRuntimeToolCall instances for the specified runtime.
            Returns empty list if no tool calls exist.

        Example:
            >>> tool_calls = repo.list_agent_runtime_tool_calls(
            ...     "my-agent", "1234567890.123"
            ... )
            >>> for tc in tool_calls:
            ...     print(f"{tc.tool_name}: {tc.status}")

        Note:
            The order of returned tool calls is not guaranteed. If you need
            chronological ordering, sort by started_at or tool_use_id.
        """
        tool_calls = []
        tool_calls_dir = self._get_tool_calls_dir(agent_id, agent_run_id)

        if not tool_calls_dir.exists():
            return tool_calls

        # Iterate through all tool call files
        for tool_call_file in tool_calls_dir.glob("tool_call_*.json"):
            if not tool_call_file.is_file():
                continue

            # Extract tool_call_id from file name
            tool_call_id = tool_call_file.stem.replace("tool_call_", "")

            # Load tool call
            tool_call = self.get_agent_runtime_tool_call(
                agent_id, agent_run_id, tool_call_id
            )
            if tool_call:
                tool_calls.append(tool_call)

        return tool_calls
