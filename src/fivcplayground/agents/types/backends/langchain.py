"""
Runnable wrapper for LangChain agents.

This module provides the AgentRunnable class, which wraps LangChain's native
agent creation functions to provide a consistent Runnable interface for FivcPlayground
agents. It handles both synchronous and asynchronous invocation with proper message
formatting and output extraction.

Core Classes:
    - AgentRunnable: Runnable wrapper for LangChain agents

Features:
    - Synchronous and asynchronous execution
    - Automatic message history management
    - Structured response support via response_model
    - Callback handler integration for monitoring
    - Multi-turn conversation support

Return Types:
    - If response_model is provided: Returns Pydantic model instance
    - If response_model is None: Returns string content from agent response

Example:
    >>> from fivcplayground.agents.types import AgentRunnable
    >>> from langchain_openai import ChatOpenAI
    >>>
    >>> # Create a model
    >>> model = ChatOpenAI(model="gpt-4o-mini")
    >>>
    >>> # Create an agent
    >>> agent = AgentRunnable(
    ...     model=model,
    ...     id="my-agent",
    ...     system_prompt="You are a helpful assistant"
    ... )
    >>> result = agent.run("Hello!")
    >>> print(result)  # Returns string
"""

import asyncio
from datetime import datetime
from typing import List, Type, Callable
from uuid import uuid4

from langchain_core.messages import (
    HumanMessage,
    BaseMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel
from langchain.agents import create_agent as lc_create_agent

from pydantic import BaseModel

from fivcplayground.agents.types import (
    AgentRunEvent,
    AgentRunStatus,
    AgentRunContent,
    AgentRun,
    AgentRunToolCall,
)
from fivcplayground.agents.types.repositories import (
    AgentRunRepository,
    AgentRunSessionSpan,
)
from fivcplayground.tools import (
    setup_tools,
    Tool,
    ToolRetriever,
)
from fivcplayground.utils import Runnable


class AgentRunnable(Runnable):
    """
    Runnable wrapper for LangChain agents.

    This class wraps LangChain's native agent creation functions to provide
    a consistent Runnable interface for FivcPlayground agents. It handles both
    synchronous and asynchronous invocation with proper message formatting
    and output extraction.

    Attributes:
        _id: Unique identifier for the runnable
        _description: Description of the agent
        _model: The underlying LangChain chat model
        _system_prompt: System prompt for the agent
    """

    def __init__(
        self,
        id: str | None = None,
        description: str | None = None,
        model: BaseChatModel | None = None,
        system_prompt: str | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        """
        Initialize AgentRunnable.

        Args:
            id: Unique identifier for the agent (auto-generated if not provided)
            description: Description of the agent
            model: LangChain chat model
            system_prompt: System prompt/instructions for the agent
            **kwargs: Additional arguments (ignored for compatibility)
        """
        self._id = id or str(uuid4())
        self._description = description or ""
        self._model = model
        self._system_prompt = system_prompt

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._id

    @property
    def description(self) -> str:
        return self._description

    def run(
        self,
        query: str | AgentRunContent = "",
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        response_model: Type[BaseModel] | None = None,
        event_callback: Callable[[AgentRunEvent, AgentRun], None] = lambda e, r: None,
        **kwargs,  # ignore additional kwargs
    ) -> BaseModel:
        return asyncio.run(
            self.run_async(
                query,
                agent_run_repository=agent_run_repository,
                agent_run_session_id=agent_run_session_id,
                tool_retriever=tool_retriever,
                response_model=response_model,
                event_callback=event_callback,
                **kwargs,
            )
        )

    async def run_async(
        self,
        query: str | AgentRunContent = "",
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        response_model: Type[BaseModel] | None = None,
        event_callback: Callable[[AgentRunEvent, AgentRun], None] = lambda e, r: None,
        **kwargs,  # ignore additional kwargs
    ) -> BaseModel:
        if query and not isinstance(query, AgentRunContent):
            query = AgentRunContent(text=str(query))

        agent_messages = _list_messages(
            agent_run_repository,
            agent_run_session_id,
            query,
        )

        async with (
            setup_tools(_list_tools(tool_retriever, query)) as tools_expanded,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self._id,
            ) as agent_run_session_span,
        ):
            agent = lc_create_agent(
                self._model,
                tools_expanded,
                name=self._id,
                system_prompt=self._system_prompt,
                response_format=response_model,
            )
            agent_run = AgentRun(
                agent_id=self._id,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            # output = None
            event_callback(AgentRunEvent.START, agent_run)

            try:
                outputs = {}
                async for mode, event_data in agent.astream(
                    agent.InputType(messages=agent_messages),
                    stream_mode=["messages", "values", "updates"],
                ):
                    event = AgentRunEvent.START

                    if mode == "values":
                        outputs = event_data

                    elif mode == "updates":
                        event = AgentRunEvent.UPDATE
                        agent_run.streaming_text = ""

                    elif mode == "messages":
                        msg, _ = event_data

                        if isinstance(msg, AIMessageChunk):
                            event = AgentRunEvent.STREAM
                            agent_run.streaming_text += msg.content

                        elif isinstance(msg, ToolMessage):
                            event = AgentRunEvent.TOOL
                            tool_call = AgentRunToolCall(
                                id=msg.tool_call_id,
                                tool_id=msg.name,
                                tool_result=msg.content,
                                started_at=datetime.now(),
                                completed_at=datetime.now(),
                                status=msg.status,
                            )
                            agent_run.tool_calls[tool_call.id] = tool_call

                    if event != AgentRunEvent.START:
                        event_callback(event, agent_run)

                    if event == AgentRunEvent.UPDATE:
                        agent_run_session_span(agent_run)

                agent_run.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                agent = lc_create_agent(
                    self._model,
                    tools_expanded,
                    name=self._id,
                    system_prompt=self._system_prompt,
                    response_format=response_model,
                )
                outputs = await agent.ainvoke(
                    agent.InputType(messages=[HumanMessage(content=error_msg)])
                )

                agent_run.status = AgentRunStatus.FAILED

            finally:
                agent_run.completed_at = datetime.now()

            if "messages" not in outputs:
                raise ValueError(f"Expected messages in outputs, got {outputs}")

            output = outputs["messages"][-1]
            if not isinstance(output, BaseMessage):
                raise ValueError(
                    f"Expected output to be BaseMessage, got {type(output)}"
                )

            agent_run.reply = AgentRunContent(text=output.content)
            event_callback(AgentRunEvent.FINISH, agent_run)

            if "structured_response" in outputs:
                output = outputs["structured_response"]
                if isinstance(output, BaseModel):
                    return output

            return agent_run.reply


def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    agent_query: AgentRunContent | None = None,
) -> List[BaseMessage]:
    agent_messages = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = agent_run_repository.list_agent_runs(agent_run_session_id)
        for m in agent_runs:
            if not m.is_completed:
                continue

            if m.query and m.query.text:
                agent_messages.append(HumanMessage(content=m.query.text))

            if m.reply and m.reply.text:
                agent_messages.append(AIMessage(content=m.reply.text))

    if agent_query:
        agent_messages.append(HumanMessage(content=str(agent_query)))
    return agent_messages


def _list_tools(
    tool_retriever: ToolRetriever | None = None,
    tool_query: AgentRunContent | None = None,
) -> List[Tool]:
    if not tool_retriever:
        return []

    if not tool_query:
        return tool_retriever.list_tools()

    return tool_retriever.retrieve_tools(str(tool_query))
