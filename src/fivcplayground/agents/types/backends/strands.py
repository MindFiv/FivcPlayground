import asyncio
from datetime import datetime
from typing import List, Type, Callable, cast
from uuid import uuid4
from warnings import warn

from pydantic import BaseModel
from strands.agent import (
    Agent,
    AgentResult,
    SlidingWindowConversationManager,
)
from strands.models import Model
from strands.types.content import Message, ContentBlock
from strands.types.tools import ToolUse, ToolResult

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
    def __init__(
        self,
        id: str | None = None,
        description: str | None = None,
        model: Model | None = None,
        system_prompt: str | None = None,
        **kwargs,  # ignore additional kwargs
    ):
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
        tool_ids: List[str] | None = None,
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
                tool_ids=tool_ids,
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
        tool_ids: List[str] | None = None,
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
            setup_tools(_list_tools(tool_retriever, tool_ids, query)) as tools_expanded,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self._id,
            ) as agent_run_session_span,
        ):
            agent = Agent(
                name=self._id,
                model=self._model,
                tools=tools_expanded,
                system_prompt=self._system_prompt,
                conversation_manager=SlidingWindowConversationManager(window_size=20),
            )
            agent_run = AgentRun(
                agent_id=self._id,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            output = None
            event_callback(AgentRunEvent.START, agent_run)

            try:
                async for event_data in agent.stream_async(
                    prompt=agent_messages,
                    structured_output_model=response_model,
                ):
                    event = AgentRunEvent.START
                    if "result" in event_data:
                        output = event_data["result"]

                    elif "data" in event_data:
                        event = AgentRunEvent.STREAM
                        agent_run.streaming_text += event_data["data"]

                    elif "message" in event_data:
                        event = AgentRunEvent.UPDATE
                        agent_run.streaming_text = ""

                        message = event_data["message"]
                        for block in message.get("content", []):
                            if "toolUse" in block:
                                event = AgentRunEvent.TOOL
                                tool_use = cast(ToolUse, block["toolUse"])
                                tool_use_id = tool_use.get("toolUseId")
                                tool_call = AgentRunToolCall(
                                    id=tool_use_id,
                                    tool_id=tool_use.get("name"),
                                    tool_input=tool_use.get("input"),
                                    started_at=datetime.now(),
                                    status=AgentRunStatus.EXECUTING,
                                )
                                agent_run.tool_calls[tool_use_id] = tool_call

                            if "toolResult" in block:
                                event = AgentRunEvent.TOOL
                                tool_result = cast(ToolResult, block["toolResult"])
                                tool_use_id = tool_result.get("toolUseId")
                                tool_call = agent_run.tool_calls.get(tool_use_id)
                                if not tool_call:
                                    warn(
                                        f"Tool result received for unknown tool call: {tool_use_id}",
                                        RuntimeWarning,
                                        stacklevel=2,
                                    )
                                    continue

                                tool_call.status = tool_result.get("status")
                                tool_call.tool_result = tool_result.get("content")
                                tool_call.completed_at = datetime.now()

                    if event != AgentRunEvent.START:
                        event_callback(event, agent_run)

                    if event == AgentRunEvent.UPDATE:
                        agent_run_session_span(agent_run)

                agent_run.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                output = await agent.invoke_async(prompt=error_msg)

                agent_run.status = AgentRunStatus.FAILED

            finally:
                agent_run.completed_at = datetime.now()

            if not isinstance(output, AgentResult):
                raise ValueError(f"Expected AgentResult, got {type(output)}")

            agent_run.reply = AgentRunContent(text=str(output))
            event_callback(AgentRunEvent.FINISH, agent_run)

            if output.structured_output:
                return output.structured_output

            return agent_run.reply


def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    agent_query: AgentRunContent | None = None,
) -> List[Message]:
    """List all messages for a specific session."""
    agent_messages = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = agent_run_repository.list_agent_runs(agent_run_session_id)
        for m in agent_runs:
            if not m.is_completed:
                continue

            if m.query and m.query.text:
                agent_messages.append(
                    Message(
                        role="user",
                        content=[ContentBlock(text=m.query.text)],
                    )
                )

            if m.reply and m.reply.text:
                agent_messages.append(
                    Message(
                        role="assistant",
                        content=[ContentBlock(text=m.reply.text)],
                    )
                )

    if agent_query:
        agent_messages.append(
            Message(
                role="user",
                content=[ContentBlock(text=str(agent_query))],
            )
        )
    return agent_messages


def _list_tools(
    tool_retriever: ToolRetriever | None = None,
    tool_ids: List[str] | None = None,
    tool_query: AgentRunContent | None = None,
) -> List[Tool]:
    if not tool_retriever:
        return []

    if tool_ids:
        tools = [tool_retriever.get_tool(name) for name in tool_ids]
        return [t for t in tools if t is not None]

    if not tool_query:
        return tool_retriever.list_tools()

    return tool_retriever.retrieve_tools(str(tool_query))
