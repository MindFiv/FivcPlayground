import asyncio
from datetime import datetime, timezone
from functools import cached_property
from typing import Optional, Callable, List

from pydantic import BaseModel

from fivcplayground.tasks import create_briefing_task
from fivcplayground.agents import (
    create_companion_agent,
    AgentRunContent,
    AgentRunSession,
    AgentRun,
    AgentRunnable,
    AgentRunRepository,
    AgentConfigRepository,
    AgentBackend,
)
from fivcplayground.models import ModelConfigRepository, ModelBackend
from fivcplayground.tools import ToolRetriever


class Chat(object):
    """
    Chat utility for handling conversation state and agent execution.
    """

    def __init__(
        self,
        agent_runnable: AgentRunnable | None = None,
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        briefing_runnable: AgentRunnable | None = None,
        tool_retriever: Optional[ToolRetriever] = None,
    ):
        assert tool_retriever is not None, "tool_retriever is required"
        assert agent_runnable is not None, "agent_runnable is required"
        assert agent_run_repository is not None, "agent_run_repository is required"
        assert briefing_runnable is not None, "briefing_runnable is required"

        self._agent_run_session_id = agent_run_session_id
        self._agent_run_repository = agent_run_repository
        self._tool_retriever = tool_retriever
        self._briefing_runnable = briefing_runnable
        self._runnable = agent_runnable
        self._running = False

    @property
    def id(self):
        return self._agent_run_session_id

    @cached_property
    def session(self):
        if not self._agent_run_session_id:
            return ""

        return self._agent_run_repository.get_agent_run_session(
            self._agent_run_session_id
        )

    @property
    def description(self):
        return self.session.description if self.session else ""

    @property
    def started_at(self):
        return self.session.started_at if self.session else ""

    @property
    def is_running(self):
        return self._running

    def list_history(self) -> List[AgentRun]:
        if not self._agent_run_session_id:
            return []

        agent_runs = self._agent_run_repository.list_agent_runs(
            self._agent_run_session_id,
        )
        return [r for r in agent_runs if r.is_completed]

    async def ask_async(
        self,
        query: str,
        on_event: Optional[Callable[[AgentRun], None]] = None,
    ) -> BaseModel:
        if self._running:
            raise ValueError("Agent is already processing a query")

        try:
            # Set running flag
            self._running = True

            # Create session ID if not exists
            agent_session_id = self._agent_run_session_id or str(
                datetime.now().timestamp()
            )
            # Execute agent with repository and tool retriever
            agent_result = await self._runnable.run_async(
                query=query,
                agent_run_repository=self._agent_run_repository,
                agent_run_session_id=agent_session_id,
                tool_retriever=self._tool_retriever,
                event_callback=lambda _, r: on_event(r),
            )
            # Save agent metadata on first query
            if not self._agent_run_session_id:
                agent_query = f"{query}\n{str(agent_result)}"
                agent_desc = await self._briefing_runnable.run_async(
                    query=agent_query,
                    tool_retriever=self._tool_retriever,
                )
                assert isinstance(agent_desc, AgentRunContent)
                self._agent_run_repository.update_agent_run_session(
                    AgentRunSession(
                        id=agent_session_id,
                        agent_id=self._runnable.id,
                        description=str(agent_desc),
                        started_at=datetime.now(),
                    )
                )
                # Update the session ID so that self.id returns the new session ID
                self._agent_run_session_id = agent_session_id

            return agent_result

        finally:
            # Always reset running flag
            self._running = False

    def ask(
        self,
        query: str,
        on_event: Optional[Callable[[AgentRun], None]] = None,
    ) -> BaseModel:
        return asyncio.run(self.ask_async(query, on_event))

    def cleanup(self) -> None:
        if self._agent_run_session_id:
            self._agent_run_repository.delete_agent_run_session(
                self._agent_run_session_id
            )


class ChatManager(object):
    def __init__(
        self,
        model_backend: ModelBackend | None = None,
        model_config_repository: ModelConfigRepository | None = None,
        agent_backend: AgentBackend | None = None,
        agent_config_repository: AgentConfigRepository | None = None,
        agent_run_repository: AgentRunRepository | None = None,
        tool_retriever: ToolRetriever | None = None,
    ):
        assert tool_retriever is not None, "tool_retriever is required"
        assert (
            model_config_repository is not None
        ), "model_config_repository is required"
        assert (
            agent_config_repository is not None
        ), "agent_config_repository is required"
        assert agent_run_repository is not None, "agent_run_repository is required"

        self._briefing_runnable = create_briefing_task(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_backend=agent_backend,
            agent_config_repository=agent_config_repository,
        )
        self._agent_runnable = create_companion_agent(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            agent_backend=agent_backend,
            agent_config_repository=agent_config_repository,
        )
        self._agent_run_repository = agent_run_repository
        self._tool_retriever = tool_retriever

    def list_chats(self) -> List[Chat]:
        chats = [
            Chat(
                agent_runnable=self._agent_runnable,
                agent_run_repository=self._agent_run_repository,
                agent_run_session_id=agent_run_session.id,
                briefing_runnable=self._briefing_runnable,
                tool_retriever=self._tool_retriever,
            )
            for agent_run_session in self._agent_run_repository.list_agent_run_sessions()
        ]
        # Sort by started_at, treating None as the earliest time (datetime.min)
        chats.sort(
            key=lambda chat: chat.started_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return chats

    def add_chat(self) -> Chat:
        return Chat(
            agent_runnable=self._agent_runnable,
            agent_run_repository=self._agent_run_repository,
            briefing_runnable=self._briefing_runnable,
            tool_retriever=self._tool_retriever,
        )
