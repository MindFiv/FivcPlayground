import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
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
from strands.types.tools import AgentTool, ToolUse, ToolResult

from fivcadvisor.agents.types import (
    AgentsEvent,
    AgentsStatus,
    AgentsContent,
    AgentsRuntime,
    AgentsRuntimeToolCall,
)
from fivcadvisor.tools.types.backends import ToolsBundle
from fivcadvisor.utils import Runnable


class AgentsRunnable(Runnable):
    def __init__(
        self,
        model: Model | None = None,
        tools: List[AgentTool] | None = None,
        agent_id: str | None = None,
        agent_name: str = "Default",
        system_prompt: str | None = None,
        messages: List[AgentsRuntime] | None = None,
        response_model: Type[BaseModel] | None = None,
        callback_handler: Callable[[AgentsEvent, AgentsRuntime], None] | None = None,
        **kwargs,
    ):
        self._id = agent_id or str(uuid4())
        self._name = agent_name
        self._system_prompt = system_prompt
        self._callback_handler = callback_handler
        self._response_model = response_model
        self._model = model
        self._tools = []
        self._tools_bundles = []
        self._messages = []

        # Separate tools and tool bundles
        for t in tools or []:
            if isinstance(t, ToolsBundle):
                self._tools_bundles.append(t)
            else:
                self._tools.append(t)

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

    @asynccontextmanager
    async def create_agent_async(self):
        """Create agent with tools loaded asynchronously."""
        async with AsyncExitStack() as stack:
            tools_expanded = [*self._tools]
            for bundle in self._tools_bundles:
                tools = await stack.enter_async_context(bundle.load_async())
                tools_expanded.extend(tools)

            yield Agent(
                agent_id=self._id,
                model=self._model,
                tools=tools_expanded,
                name=self._name,
                system_prompt=self._system_prompt,
                conversation_manager=SlidingWindowConversationManager(window_size=10),
            )

    @property
    def id(self) -> str:
        """
        Get the unique identifier for this runnable.

        Returns:
            The unique identifier string

        Example:
            >>> agent = AgentsRunnable(model=model, tools=[], agent_id="my-agent")
            >>> print(agent.id)
            'my-agent'
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Get the name of this runnable.

        Returns:
            The runnable name

        Example:
            >>> agent = AgentsRunnable(agent_name="MyAgent", model=model, tools=[])
            >>> print(agent.name)
            'MyAgent'
        """
        return self._name

    @property
    def agent_id(self):
        return self._id

    @property
    def system_prompt(self):
        return self._system_prompt

    def run(
        self,
        query: str | AgentsContent = "",
        **kwargs: Any,
    ) -> Union[BaseModel, AgentsContent]:
        return asyncio.run(self.run_async(query, **kwargs))

    async def run_async(
        self,
        query: str | AgentsContent = "",
        **kwargs: Any,
    ) -> Union[BaseModel, AgentsContent]:
        if query:
            if isinstance(query, str):
                query = AgentsContent(text=query)

            if isinstance(query, AgentsContent):
                self._messages.append(
                    Message(role="user", content=[ContentBlock(text=query.text)])
                )

        async with self.create_agent_async() as agent:
            runtime = AgentsRuntime(
                agent_id=self._id,
                agent_name=self._name,
                status=AgentsStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            output = None
            if self._callback_handler:
                self._callback_handler(AgentsEvent.START, runtime)

            try:
                async for event_data in agent.stream_async(
                    prompt=self._messages,
                    structured_output_model=self._response_model,
                ):
                    event = AgentsEvent.START
                    if "result" in event_data:
                        output = event_data["result"]

                    elif "data" in event_data:
                        event = AgentsEvent.STREAM
                        runtime.streaming_text += event_data["data"]

                    elif "message" in event_data:
                        event = AgentsEvent.UPDATE
                        runtime.streaming_text = ""

                        message = event_data["message"]
                        for block in message.get("content", []):
                            if "toolUse" in block:
                                event = AgentsEvent.TOOL
                                tool_use = cast(ToolUse, block["toolUse"])
                                tool_use_id = tool_use.get("toolUseId")
                                tool_call = AgentsRuntimeToolCall(
                                    tool_use_id=tool_use_id,
                                    tool_name=tool_use.get("name"),
                                    tool_input=tool_use.get("input"),
                                    started_at=datetime.now(),
                                    status=AgentsStatus.EXECUTING,
                                )
                                runtime.tool_calls[tool_use_id] = tool_call

                            if "toolResult" in block:
                                event = AgentsEvent.TOOL
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

                    if self._callback_handler and event != AgentsEvent.START:
                        self._callback_handler(event, runtime)

                runtime.status = AgentsStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                output = await agent.invoke_async(prompt=error_msg)

                runtime.status = AgentsStatus.FAILED

            finally:
                runtime.completed_at = datetime.now()

            if not isinstance(output, AgentResult):
                raise ValueError(f"Expected AgentResult, got {type(output)}")

            self._messages.append(output.message)

            runtime.reply = AgentsContent(text=str(output))

            if self._callback_handler:
                self._callback_handler(AgentsEvent.FINISH, runtime)

            if output.structured_output:
                return output.structured_output

            return runtime.reply
