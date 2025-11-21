import asyncio
from datetime import datetime
from typing import Any, List, Type, Union, Callable, cast
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
from fivcplayground.tools import setup_tools, Tool
from fivcplayground.utils import Runnable


class AgentRunnable(Runnable):
    def __init__(
        self,
        model: Model | None = None,
        tools: List[Tool] | None = None,
        agent_id: str | None = None,
        agent_name: str = "Default",
        system_prompt: str | None = None,
        messages: List[AgentRun] | None = None,
        response_model: Type[BaseModel] | None = None,
        callback_handler: Callable[[AgentRunEvent, AgentRun], None] | None = None,
        **kwargs,
    ):
        self._id = agent_id or str(uuid4())
        self._name = agent_name
        self._system_prompt = system_prompt
        self._callback_handler = callback_handler
        self._response_model = response_model
        self._model = model
        self._tools = tools or []
        self._messages = []

        # Convert messages to Strands format
        for m in messages or []:
            if not m.is_completed:
                continue

            if m.query and m.query.text:
                self._messages.append(
                    Message(
                        role="user",
                        content=[ContentBlock(text=m.query.text)],
                    )
                )

            if m.reply and m.reply.text:
                self._messages.append(
                    Message(
                        role="assistant",
                        content=[ContentBlock(text=m.reply.text)],
                    )
                )

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def agent_id(self):
        return self._id

    @property
    def system_prompt(self):
        return self._system_prompt

    def run(
        self,
        query: str | AgentRunContent = "",
        **kwargs: Any,
    ) -> Union[BaseModel, AgentRunContent]:
        return asyncio.run(self.run_async(query, **kwargs))

    async def run_async(
        self,
        query: str | AgentRunContent = "",
        **kwargs: Any,
    ) -> Union[BaseModel, AgentRunContent]:
        if query:
            if isinstance(query, str):
                query = AgentRunContent(text=query)

            if isinstance(query, AgentRunContent):
                self._messages.append(
                    Message(role="user", content=[ContentBlock(text=query.text)])
                )

        async with setup_tools(self._tools) as tools_expanded:
            agent = Agent(
                agent_id=self._id,
                model=self._model,
                tools=tools_expanded,
                name=self._name,
                system_prompt=self._system_prompt,
                conversation_manager=SlidingWindowConversationManager(window_size=10),
            )
            runtime = AgentRun(
                agent_id=self._id,
                agent_name=self._name,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            output = None
            if self._callback_handler:
                self._callback_handler(AgentRunEvent.START, runtime)

            try:
                async for event_data in agent.stream_async(
                    prompt=self._messages,
                    structured_output_model=self._response_model,
                ):
                    event = AgentRunEvent.START
                    if "result" in event_data:
                        output = event_data["result"]

                    elif "data" in event_data:
                        event = AgentRunEvent.STREAM
                        runtime.streaming_text += event_data["data"]

                    elif "message" in event_data:
                        event = AgentRunEvent.UPDATE
                        runtime.streaming_text = ""

                        message = event_data["message"]
                        for block in message.get("content", []):
                            if "toolUse" in block:
                                event = AgentRunEvent.TOOL
                                tool_use = cast(ToolUse, block["toolUse"])
                                tool_use_id = tool_use.get("toolUseId")
                                tool_call = AgentRunToolCall(
                                    id=tool_use_id,
                                    tool_name=tool_use.get("name"),
                                    tool_input=tool_use.get("input"),
                                    started_at=datetime.now(),
                                    status=AgentRunStatus.EXECUTING,
                                )
                                runtime.tool_calls[tool_use_id] = tool_call

                            if "toolResult" in block:
                                event = AgentRunEvent.TOOL
                                tool_result = cast(ToolResult, block["toolResult"])
                                tool_use_id = tool_result.get("toolUseId")
                                tool_call = runtime.tool_calls.get(tool_use_id)
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

                    if self._callback_handler and event != AgentRunEvent.START:
                        self._callback_handler(event, runtime)

                runtime.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                output = await agent.invoke_async(prompt=error_msg)

                runtime.status = AgentRunStatus.FAILED

            finally:
                runtime.completed_at = datetime.now()

            if not isinstance(output, AgentResult):
                raise ValueError(f"Expected AgentResult, got {type(output)}")

            self._messages.append(output.message)

            runtime.reply = AgentRunContent(text=str(output))

            if self._callback_handler:
                self._callback_handler(AgentRunEvent.FINISH, runtime)

            if output.structured_output:
                return output.structured_output

            return runtime.reply
