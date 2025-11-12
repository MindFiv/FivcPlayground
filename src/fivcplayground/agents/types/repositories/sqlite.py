"""
SQLite-based agent runtime repository implementation.

This module provides SqliteAgentsRuntimeRepository, a SQLite-based implementation
of AgentsRuntimeRepository that stores agent data in a relational database.

Database Schema:
    agents:
        - id (INTEGER PRIMARY KEY)
        - agent_id (TEXT UNIQUE NOT NULL)
        - agent_name (TEXT)
        - system_prompt (TEXT)
        - description (TEXT)
        - started_at (TIMESTAMP)
        - created_at (TIMESTAMP)

    agent_runtimes:
        - id (INTEGER PRIMARY KEY)
        - agent_run_id (TEXT UNIQUE NOT NULL)
        - agent_id (TEXT NOT NULL, FOREIGN KEY)
        - agent_name (TEXT)
        - status (TEXT)
        - started_at (TIMESTAMP)
        - completed_at (TIMESTAMP)
        - query (TEXT)
        - reply (TEXT)
        - streaming_text (TEXT)
        - error (TEXT)
        - created_at (TIMESTAMP)

    tool_calls:
        - id (INTEGER PRIMARY KEY)
        - tool_use_id (TEXT NOT NULL)
        - agent_run_id (TEXT NOT NULL, FOREIGN KEY)
        - tool_name (TEXT NOT NULL)
        - tool_input (TEXT JSON)
        - tool_result (TEXT JSON)
        - status (TEXT)
        - started_at (TIMESTAMP)
        - completed_at (TIMESTAMP)
        - error (TEXT)
        - created_at (TIMESTAMP)

This structure provides:
    - Efficient querying and filtering
    - Referential integrity with foreign keys
    - Indexed lookups for common queries
    - JSON storage for complex data types
    - Cascading deletes for data consistency

Example:
    >>> from fivcplayground.agents.types.repositories.sqlite import SqliteAgentsRuntimeRepository
    >>> from fivcplayground.agents.types import AgentsRuntimeMeta, AgentsRuntime
    >>>
    >>> # Create repository
    >>> repo = SqliteAgentsRuntimeRepository(db_path="./agents.db")
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
import os
import sqlite3
from pathlib import Path
from typing import Optional, List

from fivcplayground.agents.types import AgentsRuntimeMeta
from fivcplayground.agents.types.repositories import (
    AgentsRuntime,
    AgentsRuntimeToolCall,
    AgentsRuntimeRepository,
)
from fivcplayground.utils import OutputDir


class SqliteAgentsRuntimeRepository(AgentsRuntimeRepository):
    """
    SQLite-based repository for agent runtime data.

    Stores agent metadata, runtimes, and tool calls in a SQLite database.
    All operations are thread-safe for single-process usage.

    Attributes:
        db_path: Path to the SQLite database file
        connection: SQLite database connection

    Note:
        - All JSON serialization uses UTF-8 encoding
        - Timestamps are stored as ISO format strings
        - Corrupted JSON data is logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations use transactions for consistency
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        """
        Initialize the SQLite repository.

        Args:
            db_path: Path to the SQLite database file. Defaults to "./agents.db"

        Note:
            The database file is created automatically if it doesn't exist.
            All necessary tables are created on initialization.
        """
        output_dir = output_dir or OutputDir().subdir("agents")
        self.db_path = Path(str(os.path.join(str(output_dir), "agents.db")))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Enable foreign keys
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.row_factory = sqlite3.Row

        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.connection.cursor()

        # Create agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY,
                agent_id TEXT UNIQUE NOT NULL,
                agent_name TEXT,
                system_prompt TEXT,
                description TEXT,
                started_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create agent_runtimes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_runtimes (
                id INTEGER PRIMARY KEY,
                agent_run_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                agent_name TEXT,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                query TEXT,
                reply TEXT,
                streaming_text TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
            )
        """)

        # Create tool_calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY,
                tool_use_id TEXT NOT NULL,
                agent_run_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                tool_input TEXT,
                tool_result TEXT,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tool_use_id, agent_run_id),
                FOREIGN KEY (agent_run_id) REFERENCES agent_runtimes(agent_run_id) ON DELETE CASCADE
            )
        """)

        # Create indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_runtimes_agent_id ON agent_runtimes(agent_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_runtimes_agent_run_id ON agent_runtimes(agent_run_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_calls_agent_run_id ON tool_calls(agent_run_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_use_id ON tool_calls(tool_use_id)"
        )

        self.connection.commit()

    def update_agent(self, agent: AgentsRuntimeMeta) -> None:
        """Create or update an agent's metadata."""
        cursor = self.connection.cursor()
        agent_data = agent.model_dump(mode="json")

        # Use INSERT OR IGNORE + UPDATE instead of INSERT OR REPLACE
        # to avoid cascading deletes of related runtimes
        agent_id = agent_data.get("agent_id")

        # First, try to insert (will be ignored if already exists)
        cursor.execute(
            """
            INSERT OR IGNORE INTO agents
            (agent_id, agent_name, system_prompt, description, started_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                agent_id,
                agent_data.get("agent_name"),
                agent_data.get("system_prompt"),
                agent_data.get("description"),
                agent_data.get("started_at"),
            ),
        )

        # Then, update if it already existed
        cursor.execute(
            """
            UPDATE agents
            SET agent_name = ?, system_prompt = ?, description = ?, started_at = ?
            WHERE agent_id = ?
        """,
            (
                agent_data.get("agent_name"),
                agent_data.get("system_prompt"),
                agent_data.get("description"),
                agent_data.get("started_at"),
                agent_id,
            ),
        )
        self.connection.commit()

    def get_agent(self, agent_id: str) -> Optional[AgentsRuntimeMeta]:
        """Retrieve an agent's metadata by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()

        if not row:
            return None

        try:
            return AgentsRuntimeMeta.model_validate(
                {
                    "agent_id": row["agent_id"],
                    "agent_name": row["agent_name"],
                    "system_prompt": row["system_prompt"],
                    "description": row["description"],
                    "started_at": row["started_at"],
                }
            )
        except ValueError as e:
            print(f"Error loading agent {agent_id}: {e}")
            return None

    def list_agents(self) -> List[AgentsRuntimeMeta]:
        """List all agents in the repository."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM agents ORDER BY agent_id")
        rows = cursor.fetchall()

        agents = []
        for row in rows:
            try:
                agent = AgentsRuntimeMeta.model_validate(
                    {
                        "agent_id": row["agent_id"],
                        "agent_name": row["agent_name"],
                        "system_prompt": row["system_prompt"],
                        "description": row["description"],
                        "started_at": row["started_at"],
                    }
                )
                agents.append(agent)
            except ValueError as e:
                print(f"Error loading agent {row['agent_id']}: {e}")

        return agents

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent and all its associated runtimes."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
        self.connection.commit()

    def update_agent_runtime(self, agent_id: str, agent_runtime: AgentsRuntime) -> None:
        """Create or update an agent runtime."""
        cursor = self.connection.cursor()
        runtime_data = agent_runtime.model_dump(mode="json", exclude={"tool_calls"})

        # Ensure the agent exists (create a placeholder if needed)
        # This is necessary because of the foreign key constraint
        cursor.execute(
            """
            INSERT OR IGNORE INTO agents (agent_id, agent_name)
            VALUES (?, ?)
        """,
            (agent_id, runtime_data.get("agent_name")),
        )

        # Use the passed agent_id parameter, not the one from runtime_data
        # This ensures consistency even if agent_runtime.agent_id is None
        cursor.execute(
            """
            INSERT OR REPLACE INTO agent_runtimes
            (agent_run_id, agent_id, agent_name, status, started_at, completed_at,
             query, reply, streaming_text, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                runtime_data.get("agent_run_id"),
                agent_id,  # Use the parameter, not runtime_data.get("agent_id")
                runtime_data.get("agent_name"),
                runtime_data.get("status"),
                runtime_data.get("started_at"),
                runtime_data.get("completed_at"),
                json.dumps(runtime_data.get("query"))
                if runtime_data.get("query")
                else None,
                json.dumps(runtime_data.get("reply"))
                if runtime_data.get("reply")
                else None,
                runtime_data.get("streaming_text"),
                runtime_data.get("error"),
            ),
        )
        self.connection.commit()

    def get_agent_runtime(
        self, agent_id: str, agent_run_id: str
    ) -> Optional[AgentsRuntime]:
        """Retrieve an agent runtime by agent ID and run ID."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM agent_runtimes WHERE agent_id = ? AND agent_run_id = ?",
            (agent_id, agent_run_id),
        )
        row = cursor.fetchone()

        if not row:
            return None

        try:
            query = json.loads(row["query"]) if row["query"] else None
            reply = json.loads(row["reply"]) if row["reply"] else None

            return AgentsRuntime.model_validate(
                {
                    "agent_run_id": row["agent_run_id"],
                    "agent_id": row["agent_id"],
                    "agent_name": row["agent_name"],
                    "status": row["status"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "query": query,
                    "reply": reply,
                    "streaming_text": row["streaming_text"] or "",
                    "error": row["error"],
                }
            )
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error loading runtime {agent_run_id}: {e}")
            return None

    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """Delete an agent runtime and all its tool calls."""
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM agent_runtimes WHERE agent_id = ? AND agent_run_id = ?",
            (agent_id, agent_run_id),
        )
        self.connection.commit()

    def list_agent_runtimes(self, agent_id: str) -> List[AgentsRuntime]:
        """List all agent runtimes for a specific agent."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM agent_runtimes WHERE agent_id = ? ORDER BY agent_run_id",
            (agent_id,),
        )
        rows = cursor.fetchall()

        runtimes = []
        for row in rows:
            try:
                query = json.loads(row["query"]) if row["query"] else None
                reply = json.loads(row["reply"]) if row["reply"] else None

                runtime = AgentsRuntime.model_validate(
                    {
                        "agent_run_id": row["agent_run_id"],
                        "agent_id": row["agent_id"],
                        "agent_name": row["agent_name"],
                        "status": row["status"],
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                        "query": query,
                        "reply": reply,
                        "streaming_text": row["streaming_text"] or "",
                        "error": row["error"],
                    }
                )
                runtimes.append(runtime)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error loading runtime {row['agent_run_id']}: {e}")

        return runtimes

    def get_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call_id: str
    ) -> Optional[AgentsRuntimeToolCall]:
        """Retrieve a specific tool call by IDs."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM tool_calls WHERE agent_run_id = ? AND tool_use_id = ?",
            (agent_run_id, tool_call_id),
        )
        row = cursor.fetchone()

        if not row:
            return None

        try:
            tool_input = json.loads(row["tool_input"]) if row["tool_input"] else {}
            tool_result = json.loads(row["tool_result"]) if row["tool_result"] else None

            return AgentsRuntimeToolCall.model_validate(
                {
                    "tool_use_id": row["tool_use_id"],
                    "tool_name": row["tool_name"],
                    "tool_input": tool_input,
                    "tool_result": tool_result,
                    "status": row["status"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "error": row["error"],
                }
            )
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error loading tool call {tool_call_id}: {e}")
            return None

    def update_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call: AgentsRuntimeToolCall
    ) -> None:
        """Create or update a tool call for an agent runtime."""
        cursor = self.connection.cursor()
        tool_call_data = tool_call.model_dump(mode="json")

        # Ensure the agent exists (create a placeholder if needed)
        # This is necessary because of the foreign key constraint
        cursor.execute(
            """
            INSERT OR IGNORE INTO agents (agent_id)
            VALUES (?)
        """,
            (agent_id,),
        )

        # Ensure the runtime exists (create a placeholder if needed)
        # This is necessary because of the foreign key constraint
        cursor.execute(
            """
            INSERT OR IGNORE INTO agent_runtimes (agent_run_id, agent_id, status, streaming_text)
            VALUES (?, ?, ?, ?)
        """,
            (agent_run_id, agent_id, "pending", ""),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO tool_calls
            (tool_use_id, agent_run_id, tool_name, tool_input, tool_result,
             status, started_at, completed_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                tool_call_data.get("tool_use_id"),
                agent_run_id,
                tool_call_data.get("tool_name"),
                json.dumps(tool_call_data.get("tool_input", {})),
                json.dumps(tool_call_data.get("tool_result"))
                if tool_call_data.get("tool_result")
                else None,
                tool_call_data.get("status"),
                tool_call_data.get("started_at"),
                tool_call_data.get("completed_at"),
                tool_call_data.get("error"),
            ),
        )
        self.connection.commit()

    def list_agent_runtime_tool_calls(
        self, agent_id: str, agent_run_id: str
    ) -> List[AgentsRuntimeToolCall]:
        """List all tool calls for an agent runtime."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM tool_calls WHERE agent_run_id = ? ORDER BY created_at",
            (agent_run_id,),
        )
        rows = cursor.fetchall()

        tool_calls = []
        for row in rows:
            try:
                tool_input = json.loads(row["tool_input"]) if row["tool_input"] else {}
                tool_result = (
                    json.loads(row["tool_result"]) if row["tool_result"] else None
                )

                tool_call = AgentsRuntimeToolCall.model_validate(
                    {
                        "tool_use_id": row["tool_use_id"],
                        "tool_name": row["tool_name"],
                        "tool_input": tool_input,
                        "tool_result": tool_result,
                        "status": row["status"],
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                        "error": row["error"],
                    }
                )
                tool_calls.append(tool_call)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error loading tool call {row['tool_use_id']}: {e}")

        return tool_calls

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def __del__(self):
        """Ensure database connection is closed on object destruction."""
        self.close()
