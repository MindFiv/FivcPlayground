"""
SQLite-based agent runtime repository implementation.

This module provides SqliteAgentRunRepository, a SQLite-based implementation
of AgentRunRepository that stores agent data in a relational database.

Database Schema:
    agents:
        - id (INTEGER PRIMARY KEY)
        - agent_id (TEXT UNIQUE NOT NULL)
        - system_prompt (TEXT)
        - description (TEXT)
        - started_at (TIMESTAMP)
        - created_at (TIMESTAMP)

    agent_runtimes:
        - id (INTEGER PRIMARY KEY)
        - agent_run_id (TEXT UNIQUE NOT NULL)
        - agent_id (TEXT NOT NULL, FOREIGN KEY)
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
        - tool_call_id (TEXT NOT NULL)
        - agent_run_id (TEXT NOT NULL, FOREIGN KEY)
        - tool_id (TEXT NOT NULL)
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
    >>> from fivcplayground.agents.types.repositories.sqlite import SqliteAgentRunRepository
    >>> from fivcplayground.agents.types import AgentRunSession, AgentRun
    >>>
    >>> # Create repository
    >>> repo = SqliteAgentRunRepository(db_path="./agents.db")
    >>>
    >>> # Store agent session metadata
    >>> agent_session = AgentRunSession(
    ...     agent_id="my-agent",
    ...     description="A helpful assistant agent"
    ... )
    >>> repo.update_agent_run_session(agent_session)
    >>>
    >>> # Create and store a runtime
    >>> runtime = AgentRun(agent_id="my-agent")
    >>> repo.update_agent_run(agent_session.id, runtime)
    >>>
    >>> # List all agents
    >>> agents = repo.list_agent_run_sessions()
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List

from fivcplayground.agents.types import AgentRunSession
from fivcplayground.agents.types.repositories import (
    AgentRun,
    AgentRunToolCall,
    AgentRunRepository,
)
from fivcplayground.utils import OutputDir


class SqliteAgentRunRepository(AgentRunRepository):
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
                session_id TEXT UNIQUE,
                agent_id TEXT NOT NULL,
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
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                query TEXT,
                reply TEXT,
                streaming_text TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES agents(session_id) ON DELETE CASCADE
            )
        """)

        # Create tool_calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY,
                tool_use_id TEXT NOT NULL,
                agent_run_id TEXT NOT NULL,
                tool_id TEXT NOT NULL,
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

        # Migration: Add session_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute("PRAGMA table_info(agent_runtimes)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if "session_id" not in column_names:
                # Add session_id column with a default value
                cursor.execute(
                    "ALTER TABLE agent_runtimes ADD COLUMN session_id TEXT DEFAULT 'default-session'"
                )
        except Exception:
            # If migration fails, continue - the column might already exist
            pass

        # Migration: Rename tool_name to tool_id in tool_calls table (for existing databases)
        try:
            cursor.execute("PRAGMA table_info(tool_calls)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if "tool_name" in column_names and "tool_id" not in column_names:
                # Rename tool_name to tool_id
                cursor.execute(
                    "ALTER TABLE tool_calls RENAME COLUMN tool_name TO tool_id"
                )
        except Exception:
            # If migration fails, continue - the column might already be renamed
            pass

        # Create indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_runtimes_session_id ON agent_runtimes(session_id)"
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

    def update_agent_run_session(self, agent: AgentRunSession) -> None:
        """Create or update an agent's metadata."""
        cursor = self.connection.cursor()
        agent_data = agent.model_dump(mode="json")

        # Use INSERT OR IGNORE + UPDATE instead of INSERT OR REPLACE
        # to avoid cascading deletes of related runtimes
        session_id = agent_data.get("id")
        agent_id = agent_data.get("agent_id")

        # First, try to insert (will be ignored if already exists)
        cursor.execute(
            """
            INSERT OR IGNORE INTO agents
            (session_id, agent_id, description, started_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                session_id,
                agent_id,
                agent_data.get("description"),
                agent_data.get("started_at"),
            ),
        )

        # Then, update if it already existed
        cursor.execute(
            """
            UPDATE agents
            SET description = ?, started_at = ?
            WHERE session_id = ?
        """,
            (
                agent_data.get("description"),
                agent_data.get("started_at"),
                session_id,
            ),
        )
        self.connection.commit()

    def get_agent_run_session(self, session_id: str) -> Optional[AgentRunSession]:
        """Retrieve an agent session's metadata by session ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM agents WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            return None

        try:
            return AgentRunSession.model_validate(
                {
                    "id": row["session_id"],
                    "agent_id": row["agent_id"],
                    "description": row["description"],
                    "started_at": row["started_at"],
                }
            )
        except ValueError as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def list_agent_run_sessions(self) -> List[AgentRunSession]:
        """List all agents in the repository."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM agents ORDER BY agent_id")
        rows = cursor.fetchall()

        agents = []
        for row in rows:
            try:
                agent = AgentRunSession.model_validate(
                    {
                        "agent_id": row["agent_id"],
                        "description": row["description"],
                        "started_at": row["started_at"],
                    }
                )
                agents.append(agent)
            except ValueError as e:
                print(f"Error loading agent {row['agent_id']}: {e}")

        return agents

    def delete_agent_run_session(self, session_id: str) -> None:
        """Delete an agent session and all its associated runtimes."""
        cursor = self.connection.cursor()
        # Delete all runtimes for this session (which will cascade delete tool calls)
        cursor.execute("DELETE FROM agent_runtimes WHERE session_id = ?", (session_id,))
        # Delete the agent metadata
        cursor.execute("DELETE FROM agents WHERE session_id = ?", (session_id,))
        self.connection.commit()

    def update_agent_run(self, session_id: str, agent_run: AgentRun) -> None:
        """Create or update an agent runtime with embedded tool calls.

        Note:
            streaming_text is excluded from serialization and will not be stored
            in the database. It is only used for in-memory streaming during execution.
        """
        cursor = self.connection.cursor()
        runtime_data = agent_run.model_dump(mode="json", exclude={"tool_calls"})

        # Get agent_id from the runtime data
        agent_id = runtime_data.get("agent_id")

        # Ensure the agent exists (create a placeholder if needed)
        # This is necessary because of the foreign key constraint
        if agent_id and session_id:
            cursor.execute(
                """
                INSERT OR IGNORE INTO agents (session_id, agent_id)
                VALUES (?, ?)
            """,
                (session_id, agent_id),
            )

        # Use the passed session_id parameter for grouping runtimes
        cursor.execute(
            """
            INSERT OR REPLACE INTO agent_runtimes
            (agent_run_id, session_id, agent_id, status, started_at, completed_at,
             query, reply, streaming_text, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                runtime_data.get("id"),
                session_id,
                agent_id,
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

        # Store embedded tool calls in the tool_calls table
        agent_run_id = runtime_data.get("id")
        for tool_call_id, tool_call in agent_run.tool_calls.items():
            tool_call_data = tool_call.model_dump(mode="json")
            cursor.execute(
                """
                INSERT OR REPLACE INTO tool_calls
                (tool_use_id, agent_run_id, tool_id, tool_input, tool_result,
                 status, started_at, completed_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    tool_call_data.get("id"),
                    agent_run_id,
                    tool_call_data.get("tool_id"),
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

    def get_agent_run(self, session_id: str, run_id: str) -> Optional[AgentRun]:
        """Retrieve an agent runtime by session ID and run ID with embedded tool calls.

        Note:
            streaming_text is excluded from serialization and will be empty string
            when loaded from the database. It is only used for in-memory streaming.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM agent_runtimes WHERE session_id = ? AND agent_run_id = ?",
            (session_id, run_id),
        )
        row = cursor.fetchone()

        if not row:
            return None

        try:
            query = json.loads(row["query"]) if row["query"] else None
            reply = json.loads(row["reply"]) if row["reply"] else None

            # Load embedded tool calls
            cursor.execute(
                "SELECT * FROM tool_calls WHERE agent_run_id = ? ORDER BY created_at",
                (run_id,),
            )
            tool_call_rows = cursor.fetchall()

            tool_calls = {}
            for tc_row in tool_call_rows:
                try:
                    tool_input = (
                        json.loads(tc_row["tool_input"]) if tc_row["tool_input"] else {}
                    )
                    tool_result = (
                        json.loads(tc_row["tool_result"])
                        if tc_row["tool_result"]
                        else None
                    )

                    tool_call = AgentRunToolCall.model_validate(
                        {
                            "id": tc_row["tool_use_id"],
                            "tool_id": tc_row["tool_id"],
                            "tool_input": tool_input,
                            "tool_result": tool_result,
                            "status": tc_row["status"],
                            "started_at": tc_row["started_at"],
                            "completed_at": tc_row["completed_at"],
                            "error": tc_row["error"],
                        }
                    )
                    tool_calls[tc_row["tool_use_id"]] = tool_call
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Error loading tool call {tc_row['tool_use_id']}: {e}")

            return AgentRun.model_validate(
                {
                    "id": row["agent_run_id"],
                    "agent_id": row["agent_id"],
                    "status": row["status"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "query": query,
                    "reply": reply,
                    "streaming_text": row["streaming_text"] or "",
                    "error": row["error"],
                    "tool_calls": tool_calls,
                }
            )
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error loading runtime {run_id}: {e}")
            return None

    def delete_agent_run(self, session_id: str, run_id: str) -> None:
        """Delete an agent runtime and all its tool calls."""
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM agent_runtimes WHERE session_id = ? AND agent_run_id = ?",
            (session_id, run_id),
        )
        self.connection.commit()

    def list_agent_runs(self, session_id: str) -> List[AgentRun]:
        """List all agent runtimes for a specific session with embedded tool calls."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM agent_runtimes WHERE session_id = ? ORDER BY agent_run_id",
            (session_id,),
        )
        rows = cursor.fetchall()

        runtimes = []
        for row in rows:
            try:
                query = json.loads(row["query"]) if row["query"] else None
                reply = json.loads(row["reply"]) if row["reply"] else None

                # Load embedded tool calls for this runtime
                cursor.execute(
                    "SELECT * FROM tool_calls WHERE agent_run_id = ? ORDER BY created_at",
                    (row["agent_run_id"],),
                )
                tool_call_rows = cursor.fetchall()

                tool_calls = {}
                for tc_row in tool_call_rows:
                    try:
                        tool_input = (
                            json.loads(tc_row["tool_input"])
                            if tc_row["tool_input"]
                            else {}
                        )
                        tool_result = (
                            json.loads(tc_row["tool_result"])
                            if tc_row["tool_result"]
                            else None
                        )

                        tool_call = AgentRunToolCall.model_validate(
                            {
                                "id": tc_row["tool_use_id"],
                                "tool_id": tc_row["tool_id"],
                                "tool_input": tool_input,
                                "tool_result": tool_result,
                                "status": tc_row["status"],
                                "started_at": tc_row["started_at"],
                                "completed_at": tc_row["completed_at"],
                                "error": tc_row["error"],
                            }
                        )
                        tool_calls[tc_row["tool_use_id"]] = tool_call
                    except (ValueError, json.JSONDecodeError) as e:
                        print(f"Error loading tool call {tc_row['tool_use_id']}: {e}")

                runtime = AgentRun.model_validate(
                    {
                        "id": row["agent_run_id"],
                        "agent_id": row["agent_id"],
                        "status": row["status"],
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                        "query": query,
                        "reply": reply,
                        "streaming_text": row["streaming_text"] or "",
                        "error": row["error"],
                        "tool_calls": tool_calls,
                    }
                )
                runtimes.append(runtime)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error loading runtime {row['agent_run_id']}: {e}")

        return runtimes

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def __del__(self):
        """Ensure database connection is closed on object destruction."""
        self.close()
