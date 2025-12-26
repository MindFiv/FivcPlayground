"""
File-based agent repository implementations.

This module provides two separate file-based repository implementations:

1. **FileAgentConfigRepository**: Stores simple agent configurations
   - Stores: agent id, name, description, system_prompt
   - Use case: Configuration management for agents
   - Storage: Single consolidated YAML file with all agent configurations

2. **FileAgentRunRepository**: Stores agent runtime execution data
   - Stores: agent metadata, execution runs, tool calls, execution state
   - Use case: Tracking agent execution history and performance
   - Storage: Hierarchical directory structure with nested runs and tool calls

FileAgentConfigRepository uses YAML files with UTF-8 encoding and is thread-safe
for single-process usage. FileAgentRunRepository uses JSON files.

FileAgentConfigRepository Storage Structure:
    /<output_dir>/
    └── agents.yaml    # All agent configurations (mapping of agent_id -> AgentConfig)

FileAgentRunRepository Storage Structure:
    /<output_dir>/
    └── session_<session_id>/
        ├── session.json             # Agent metadata (AgentRunSession)
        └── run_<agent_run_id>.json  # Agent Runtime metadata (AgentRun) with embedded tool calls
"""

import yaml
import json
import shutil
from pathlib import Path
from typing import Optional, List

from fivcplayground.agents.types import AgentRunSession
from fivcplayground.utils import OutputDir

from fivcplayground.agents.types.repositories.base import (
    AgentConfig,
    AgentConfigRepository,
    AgentRun,
    AgentRunRepository,
)


class FileAgentConfigRepository(AgentConfigRepository):
    """
    File-based repository for agent configurations.

    Stores all agent configurations in a single consolidated YAML file.
    This repository is designed for configuration management and is separate
    from FileAgentRunRepository which handles runtime execution data.

    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/
        └── agents.yaml    # All agent configurations (mapping of agent_id -> AgentConfig)

    Data stored per agent:
        - id: Unique agent identifier
        - name: Agent display name (computed from id)
        - model_id: Optional model identifier
        - tool_ids: Optional list of tool IDs to use with the agent
        - description: Optional agent description
        - system_prompt: Optional system prompt for the agent

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root
        agents_file: Path to the agents.yaml file

    Note:
        - YAML file uses UTF-8 encoding
        - Corrupted YAML files are logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations create necessary directories automatically
        - This repository stores ONLY configuration, not execution data
        - For runtime execution data, use FileAgentRunRepository instead

    Example:
        >>> from fivcplayground.agents.types.repositories.files import FileAgentConfigRepository
        >>> from fivcplayground.agents.types.base import AgentConfig
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create repository
        >>> repo = FileAgentConfigRepository()
        >>>
        >>> # Store agent configuration
        >>> config = AgentConfig(
        ...     id="assistant-v1",
        ...     description="Main assistant",
        ...     system_prompt="You are helpful"
        ... )
        >>> repo.update_agent_config(config)
        >>>
        >>> # Retrieve configuration
        >>> retrieved = repo.get_agent_config("assistant-v1")
        >>> all_configs = repo.list_agent_configs()
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        """
        Initialize the file-based repository.

        Args:
            output_dir: Optional OutputDir for the repository. If not provided,
                       defaults to OutputDir().subdir("configs")

        Note:
            The base directory is created automatically if it doesn't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("configs")
        self.base_path = Path(str(self.output_dir))
        self.agents_file = self.base_path / "agents.yaml"

        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_agents_file(self) -> Path:
        """
        Get the file path for the consolidated agents YAML file.

        Returns:
            Path to agents.yaml file
        """
        return self.agents_file

    def _load_agents_data(self) -> dict:
        """
        Load all agents from the YAML file.

        Returns:
            Dictionary mapping agent_id to agent configuration data.
            Returns empty dict if file doesn't exist or is corrupted.
        """
        agents_file = self._get_agents_file()
        if not agents_file.exists():
            return {}
        try:
            with open(agents_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except (yaml.YAMLError, ValueError) as e:
            print(f"Error loading agents from {agents_file.name}: {e}")
            return {}

    def _save_agents_data(self, agents_data: dict) -> None:
        """
        Save all agents to the YAML file.

        Args:
            agents_data: Dictionary mapping agent_id to agent configuration data
        """
        agents_file = self._get_agents_file()
        with open(agents_file, "w", encoding="utf-8") as f:
            yaml.dump(agents_data, f, default_flow_style=False, allow_unicode=True)

    def update_agent_config(self, agent_config: AgentConfig) -> None:
        """
        Create or update an agent configuration.

        Stores agent configuration in the consolidated YAML file. The agent_id
        is derived from the agent_config.id field.

        Args:
            agent_config: AgentConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same agent will overwrite the existing configuration.
        """
        agent_id = agent_config.id

        # Load all agents, update the one we're saving, and save back
        agents_data = self._load_agents_data()
        agent_data = agent_config.model_dump(mode="json")
        agents_data[agent_id] = agent_data
        self._save_agents_data(agents_data)

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Retrieve an agent configuration by ID.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            AgentConfig instance if found, None if agent doesn't exist
            or if the YAML file is corrupted
        """
        agents_data = self._load_agents_data()

        if agent_id not in agents_data:
            return None

        try:
            agent_data = agents_data[agent_id]
            agent_data["id"] = agent_id
            return AgentConfig.model_validate(agent_data)
        except ValueError as e:
            print(f"Error loading agent config {agent_id}: {e}")
            return None

    def list_agent_configs(self) -> List[AgentConfig]:
        """
        List all agent configurations in the repository.

        Returns:
            List of AgentConfig instances sorted by agent_id.
            Returns empty list if no agents exist.
        """
        agents_data = self._load_agents_data()
        configs = []

        for agent_id in sorted(agents_data.keys()):
            try:
                agent_data = agents_data[agent_id]
                agent_data["id"] = agent_id
                config = AgentConfig.model_validate(agent_data)
                configs.append(config)
            except ValueError as e:
                print(f"Error loading agent config {agent_id}: {e}")

        return configs

    def delete_agent_config(self, agent_id: str) -> None:
        """
        Delete an agent configuration.

        Args:
            agent_id: Unique identifier for the agent to delete

        Note:
            This operation is safe to call on non-existent agents.
        """
        agents_data = self._load_agents_data()
        if agent_id in agents_data:
            del agents_data[agent_id]
            self._save_agents_data(agents_data)


class FileAgentRunRepository(AgentRunRepository):
    """
    File-based repository for agent runtime execution data.

    Stores agent metadata and execution runs with embedded tool calls in a
    simplified directory structure with JSON files. This repository is designed
    for tracking agent execution history and performance, and is separate from
    FileAgentConfigRepository which handles simple agent configurations.

    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/
        └── session_<session_id>/
            ├── session.json             # Agent metadata (AgentRunSession)
            └── run_<agent_run_id>.json  # Agent Runtime metadata (AgentRun) with embedded tool calls

    Data stored per agent:
        - Agent metadata: agent_id, description, started_at
        - Runtimes: execution status, timestamps, streaming text, tool calls (embedded)
        - Tool calls: stored as part of AgentRun.tool_calls dictionary

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root

    Note:
        - All JSON files use UTF-8 encoding with 2-space indentation
        - Corrupted JSON files are logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations create necessary directories automatically
        - This repository stores ONLY runtime execution data
        - For agent configuration, use FileAgentConfigRepository instead
        - Supports cascading deletes (deleting an agent removes all its runtimes)
        - Tool calls are embedded within AgentRun objects, not stored separately

    Example:
        >>> from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
        >>> from fivcplayground.agents.types import AgentRunSession, AgentRun, AgentRunToolCall
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create repository
        >>> repo = FileAgentRunRepository(output_dir=OutputDir("./agent_runs"))
        >>>
        >>> # Store agent session metadata
        >>> agent_session = AgentRunSession(
        ...     agent_id="my-agent",
        ...     description="A helpful assistant agent"
        ... )
        >>> repo.update_agent_run_session(agent_session)
        >>>
        >>> # Create and store a runtime execution with embedded tool calls
        >>> runtime = AgentRun(agent_id="my-agent")
        >>> tool_call = AgentRunToolCall(id="call-1", tool_id="calculator")
        >>> runtime.tool_calls["call-1"] = tool_call
        >>> repo.update_agent_run(agent_session.id, runtime)
        >>>
        >>> # List all agents and their runtimes
        >>> agents = repo.list_agent_run_sessions()
        >>> runtimes = repo.list_agent_runs(agent_session.id)
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
        self.output_dir = output_dir or OutputDir().subdir("agent_runs")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_session_dir(self, session_id: str) -> Path:
        """
        Get the directory path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to session directory (e.g., /<base_path>/session_<session_id>/)
        """
        return self.base_path / f"session_{session_id}"

    def _get_session_file(self, session_id: str) -> Path:
        """
        Get the file path for session metadata.

        Args:
            session_id: Session identifier

        Returns:
            Path to session metadata file (e.g., /<base_path>/session_<session_id>/session.json)
        """
        return self._get_session_dir(session_id) / "session.json"

    def _get_run_file(self, session_id: str, agent_run_id: str) -> Path:
        """
        Get the file path for agent runtime metadata with embedded tool calls.

        Args:
            session_id: Session identifier
            agent_run_id: Agent run identifier

        Returns:
            Path to runtime file (e.g., /<base_path>/session_<session_id>/run_<agent_run_id>.json)
        """
        return self._get_session_dir(session_id) / f"run_{agent_run_id}.json"

    def update_agent_run_session(self, agent: AgentRunSession) -> None:
        """
        Create or update an agent's metadata.

        Stores agent configuration including agent_id and description in session.json
        file. Creates the session directory if it doesn't exist.

        Args:
            agent: AgentRunSession instance containing agent configuration

        Example:
            >>> agent_session = AgentRunSession(
            ...     agent_id="my-agent",
            ...     description="A helpful assistant"
            ... )
            >>> repo.update_agent_run_session(agent_session)

        Note:
            This operation is idempotent - calling it multiple times with the
            same session id will overwrite the existing metadata.
        """
        session_dir = self._get_session_dir(agent.id)
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = self._get_session_file(agent.id)

        # Serialize agent metadata to JSON
        agent_data = agent.model_dump(mode="json")

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)

    def get_agent_run_session(self, session_id: str) -> Optional[AgentRunSession]:
        """
        Retrieve an agent session's metadata by session ID.

        Reads and deserializes the session.json file for the specified session.

        Args:
            session_id: Unique identifier for the session

        Returns:
            AgentRunSession instance if found, None if session doesn't exist
            or if the session.json file is corrupted

        Example:
            >>> session = repo.get_agent_run_session("1234567890.123")
            >>> if session:
            ...     print(f"Agent: {session.agent_id}")

        Note:
            Corrupted JSON files are logged to stdout and return None.
        """
        if not self.base_path.exists():
            return None

        session_dir = self._get_session_dir(session_id)
        session_file = session_dir / "session.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Reconstruct AgentRunSession from JSON
            return AgentRunSession.model_validate(session_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading session from {session_file}: {e}")
            return None

    def list_agent_run_sessions(self) -> List[AgentRunSession]:
        """
        List all agents in the repository.

        Scans all session_* directories and loads their metadata. Corrupted
        session files are skipped.

        Returns:
            List of AgentRunSession instances sorted by agent_id.
            Returns empty list if no agents exist or repository is empty.

        Example:
            >>> agents = repo.list_agent_run_sessions()
            >>> for agent in agents:
            ...     print(f"{agent.agent_id}: {agent.id}")

        Note:
            Results are sorted alphabetically by agent_id for consistent ordering.
        """
        agents = []

        if not self.base_path.exists():
            return agents

        # Iterate through all session directories
        for session_dir in self.base_path.glob("session_*"):
            if not session_dir.is_dir():
                continue

            session_file = session_dir / "session.json"
            if not session_file.exists():
                continue

            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    agent_data = json.load(f)

                agent = AgentRunSession.model_validate(agent_data)
                agents.append(agent)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading session from {session_file}: {e}")

        # Sort by agent_id for consistent ordering
        agents.sort(key=lambda a: a.agent_id)

        return agents

    def delete_agent_run_session(self, session_id: str) -> None:
        """
        Delete an agent session and all its associated runtimes.

        This is a cascading delete operation that removes:
            - Agent metadata (session.json)
            - All agent runtimes for this session

        Args:
            session_id: Unique identifier for the session to delete

        Example:
            >>> repo.delete_agent_run_session("1234567890.123")
            >>> # All data for this session is now deleted

        Note:
            This operation is safe to call on non-existent sessions - it will
            not raise an error if the session doesn't exist.
        """
        if not self.base_path.exists():
            return

        session_dir = self._get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

    def update_agent_run(self, session_id: str, agent_run: AgentRun) -> None:
        """
        Create or update an agent runtime.

        Stores runtime execution metadata including status, timestamps, streaming text,
        and embedded tool calls.

        Args:
            session_id: Session ID that owns this runtime
            agent_run: AgentRun instance to persist (with embedded tool_calls)

        Example:
            >>> runtime = AgentRun(
            ...     agent_id="my-agent",
            ...     status=AgentRunStatus.EXECUTING
            ... )
            >>> tool_call = AgentRunToolCall(id="call-1", tool_id="calculator")
            >>> runtime.tool_calls["call-1"] = tool_call
            >>> repo.update_agent_run(session.id, runtime)

        Note:
            This operation is idempotent - calling it multiple times with the
            same id will overwrite the existing runtime metadata.
            Creates the session directory if it doesn't exist.
            Tool calls are embedded within the AgentRun object.
        """
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        run_file = self._get_run_file(session_id, str(agent_run.id))

        # Serialize agent to JSON (include tool_calls as they're now embedded)
        # Note: streaming_text is excluded from serialization by Pydantic configuration
        agent_data = agent_run.model_dump(mode="json")

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)

    def get_agent_run(self, session_id: str, run_id: str) -> Optional[AgentRun]:
        """
        Retrieve an agent runtime by session ID and run ID.

        Reads and deserializes the run.json file for the specified runtime.
        Tool calls are included as embedded data within the AgentRun object.

        Args:
            session_id: Session ID that owns the runtime
            run_id: Unique identifier for the runtime instance

        Returns:
            AgentRun instance if found (with embedded tool_calls), None if runtime
            doesn't exist or if the run.json file is corrupted

        Example:
            >>> runtime = repo.get_agent_run(session.id, "1234567890.123")
            >>> if runtime:
            ...     print(f"Status: {runtime.status}")
            ...     print(f"Tool calls: {len(runtime.tool_calls)}")

        Note:
            Tool calls are embedded within the AgentRun object.
            Corrupted JSON files are logged to stdout and return None.
            streaming_text is excluded from serialization and will be empty string
            when loaded from the file. It is only used for in-memory streaming.
        """
        run_file = self._get_run_file(session_id, run_id)

        if not run_file.exists():
            return None

        try:
            with open(run_file, "r", encoding="utf-8") as f:
                agent_data = json.load(f)

            # Reconstruct AgentRun from JSON (includes embedded tool_calls)
            # streaming_text will be set to default value (empty string) since it's excluded
            return AgentRun.model_validate(agent_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading session {session_id} run {run_id}: {e}")
            return None

    def delete_agent_run(self, session_id: str, run_id: str) -> None:
        """
        Delete an agent runtime and all its embedded tool calls.

        Removes the runtime metadata file (run.json) which contains the embedded
        tool calls.

        Args:
            session_id: Session ID that owns the runtime
            run_id: Unique identifier for the runtime to delete

        Example:
            >>> repo.delete_agent_run(session.id, "1234567890.123")
            >>> # Runtime and all its embedded tool calls are now deleted

        Note:
            This operation is safe to call on non-existent runtimes - it will
            not raise an error if the runtime doesn't exist.
        """
        run_file = self._get_run_file(session_id, run_id)

        if run_file.exists():
            run_file.unlink()

    def list_agent_runs(self, session_id: str) -> List[AgentRun]:
        """
        List all agent runtimes for a specific session in chronological order.

        Scans all run_*.json files in the session directory for the specified session
        and loads their metadata. Corrupted runtime files are skipped.

        Args:
            session_id: Session ID to list runtimes for

        Returns:
            List of AgentRun instances sorted by id (timestamp)
            in increasing order. Returns empty list if no runtimes exist.

        Example:
            >>> runtimes = repo.list_agent_runs(session.id)
            >>> for runtime in runtimes:
            ...     print(f"{runtime.id}: {runtime.status}")

        Note:
            Results are sorted chronologically by id (timestamp string)
            for consistent ordering. Earlier runs appear first in the list.
        """
        runtimes = []

        session_dir = self._get_session_dir(session_id)

        if not session_dir.exists():
            return runtimes

        # Iterate through all run_*.json files in the session directory
        for run_file in session_dir.glob("run_*.json"):
            if not run_file.is_file():
                continue

            try:
                with open(run_file, "r", encoding="utf-8") as f:
                    runtime_data = json.load(f)

                runtime = AgentRun.model_validate(runtime_data)
                runtimes.append(runtime)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading runtime from {run_file}: {e}")

        # Sort by id (timestamp string) in increasing order
        runtimes.sort(key=lambda r: r.id)

        return runtimes
