import asyncio
from datetime import datetime
from typing import List, Type, Callable, cast
from warnings import warn

from pydantic import BaseModel
from strands.agent import (
    Agent as StrandsAgentUnderlying,
    AgentResult as StrandsAgentResult,
    SlidingWindowConversationManager,
)
from strands.models import Model as StrandsModelUnderlying
from strands.types.content import Message, ContentBlock
from strands.types.tools import ToolUse, ToolResult

from fivcplayground.agents import (
    AgentConfig,
    AgentRunEvent,
    AgentRunStatus,
    AgentRunContent,
    AgentRun,
    AgentRunnable,
    AgentRunToolCall,
    AgentRunRepository,
    AgentBackend,
    AgentRunToolSpan,
    AgentRunSessionSpan,
)
from fivcplayground.models import Model
from fivcplayground.tools import ToolRetriever


def _to_content_blocks(content: AgentRunContent) -> list[ContentBlock]:
    """Convert AgentRunContent to list of ContentBlock."""
    blocks = []
    if content.text:
        blocks.append(ContentBlock(text=content.text))

    # for img in content.images:
    #     blocks.append(ContentBlock(image={"source": img, "format": ""}))

    return blocks


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

            if m.query:
                agent_messages.append(
                    Message(
                        role="user",
                        content=_to_content_blocks(m.query),
                    )
                )

            if m.reply:
                agent_messages.append(
                    Message(
                        role="assistant",
                        content=_to_content_blocks(m.reply),
                    )
                )

    if agent_query:
        agent_messages.append(
            Message(
                role="user",
                content=_to_content_blocks(agent_query),
            )
        )
    return agent_messages


class StrandsAgentRunnable(AgentRunnable):
    def __init__(
        self,
        agent_config: AgentConfig,
        agent_model: StrandsModelUnderlying,
        **kwargs,  # ignore additional kwargs
    ):
        self._agent_config = agent_config
        self._agent_model = agent_model

    @property
    def id(self) -> str:
        return self._agent_config.id

    @property
    def name(self) -> str:
        return self._agent_config.name

    @property
    def description(self) -> str:
        return self._agent_config.description

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
            AgentRunToolSpan(
                tool_retriever,
                tool_ids or self._agent_config.tool_ids,
                query,
            ) as tools_expanded,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self.id,
            ) as agent_run_session_span,
        ):
            agent = StrandsAgentUnderlying(
                name=self.id,
                model=self._agent_model,
                tools=[t.get_underlying() for t in tools_expanded]
                or [
                    tool_retriever.to_tool().get_underlying()
                ],  # always pass at least a tool
                system_prompt=self._agent_config.system_prompt,
                conversation_manager=SlidingWindowConversationManager(window_size=20),
            )
            agent_run = AgentRun(
                agent_id=self.id,
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

                # Ensure reply is set and FINISH event is called even if an exception occurred
                if isinstance(output, StrandsAgentResult):
                    agent_run.reply = AgentRunContent(text=str(output))
                else:
                    agent_run.error = f"Expected AgentResult, got {type(output)}"
                    agent_run.status = AgentRunStatus.FAILED

                event_callback(AgentRunEvent.FINISH, agent_run)

                # Save the final agent run state to the repository
                agent_run_session_span(agent_run)

            # Return structured output if available, otherwise return reply
            if isinstance(output, StrandsAgentResult) and output.structured_output:
                return output.structured_output

            return agent_run.reply if agent_run.reply else AgentRunContent(text="")


class StrandsAgentBackend(AgentBackend):
    """Agent backend for strands"""

    def create_agent(
        self,
        agent_model: Model,
        agent_config: AgentConfig,
    ) -> AgentRunnable:
        """Create an agent instance from an AgentConfig."""
        agent_model = agent_model.get_underlying()
        if not isinstance(agent_model, StrandsModelUnderlying):
            raise RuntimeError(
                f"Expected StrandsModelUnderlying, got {type(agent_model)}"
            )
        return StrandsAgentRunnable(agent_config, agent_model)
