import asyncio
import json
from datetime import datetime
from string import Template
from typing import Any, AsyncIterator, Callable, List, Type
from uuid import uuid4
from warnings import warn

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.agent import CallToolsNode, ModelRequestNode
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    TextPartDelta,
    ToolReturnPart,
)
from pydantic_ai.models import Model as PydanticAIModelUnderlying
from pydantic_ai.toolsets.abstract import AbstractToolset

from fivcplayground.agents import (
    AgentBackend,
    AgentConfig,
    AgentRun,
    AgentRunContent,
    AgentRunEvent,
    AgentRunnable,
    AgentRunRepository,
    AgentRunSessionSpan,
    AgentRunStatus,
    AgentRunToolCall,
    AgentRunToolSpan,
    AgentRunSkillSpan,
)
from fivcplayground.models import (
    ModelBackend,
    ModelConfigRepository,
    create_model_async,
)
from fivcplayground.skills import SkillRetriever
from fivcplayground.tools import ToolRetriever


async def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
) -> list[ModelMessage]:
    """Map persisted completed runs to Pydantic AI message history."""
    agent_messages: list[ModelMessage] = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = await agent_run_repository.list_agent_runs_async(
            agent_run_session_id
        )
        for run in agent_runs:
            if not run.is_completed:
                continue

            if run.query and run.query.text:
                agent_messages.append(ModelRequest.user_text_prompt(run.query.text))

            if run.reply:
                reply_text = run.reply.text
                if not reply_text and run.reply.structured is not None:
                    reply_text = json.dumps(
                        run.reply.structured,
                        ensure_ascii=False,
                    )
                if reply_text:
                    agent_messages.append(
                        ModelResponse(parts=[TextPart(content=reply_text)])
                    )

    return agent_messages


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _tool_result_value(part: ToolReturnPart) -> Any:
    """Return a compact JSON-compatible representation of a tool result."""
    if isinstance(part.content, (str, int, float, bool)) or part.content is None:
        return part.content
    return part.model_response_object()


def _tool_error_value(part: ToolReturnPart | RetryPromptPart) -> str:
    if isinstance(part, RetryPromptPart):
        return str(part.content)
    return part.model_response_str(wrap_if_error=False)


class PydanticAIAgentRunnable(AgentRunnable):
    """Agent runnable backed by Pydantic AI."""

    def __init__(
        self,
        agent_config: AgentConfig,
        agent_model: PydanticAIModelUnderlying,
        **kwargs,  # ignore additional kwargs
    ):
        del kwargs
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

    async def stream_async(
        self,
        query: str | AgentRunContent = "",
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        agent_run_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
        skill_ids: List[str] | None = None,
        response_model: Type[BaseModel] | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,  # ignore additional kwargs
    ) -> AsyncIterator[tuple[AgentRunEvent, AgentRun]]:
        """Execute the Pydantic AI agent and yield domain run events."""
        del kwargs
        response_model = (
            response_model
            if response_model is not None
            else self._agent_config.response_model
        )

        if query and not isinstance(query, AgentRunContent):
            query = AgentRunContent(text=str(query))

        agent_messages = await _list_messages(
            agent_run_repository,
            agent_run_session_id,
        )

        agent_tool_ids = set(tool_ids) if tool_ids else set()
        agent_tool_ids.update(self._agent_config.tool_ids or [])

        agent_skill_ids = set(skill_ids) if skill_ids else set()
        agent_skill_ids.update(self._agent_config.skill_ids or [])

        async with (
            AgentRunToolSpan(
                tool_retriever=tool_retriever,
                tool_ids=list(agent_tool_ids),
                context=context,
            ) as agent_tool_span,
            AgentRunSkillSpan(
                skill_retriever=skill_retriever,
                skill_ids=list(agent_skill_ids),
            ) as agent_skill_span,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self.id,
            ) as agent_run_session_span,
        ):
            if agent_skill_span.get_skill_paths():
                raise RuntimeError(
                    "The Pydantic AI backend only supports inline skills; "
                    "path-based skills are not supported."
                )

            agent_tools = []
            agent_toolsets = []

            def register_underlying_tool(tool: Any) -> None:
                underlying = tool.get_underlying()
                if isinstance(underlying, AbstractToolset):
                    agent_toolsets.append(underlying)
                else:
                    agent_tools.append(underlying)

            for tool in agent_tool_span.tools:
                register_underlying_tool(tool)

            await agent_skill_span.register_skills_async(
                agent_tool_span=agent_tool_span,
                agent_tool_register=register_underlying_tool,
            )

            agent = Agent(
                self._agent_model,
                name=self.id,
                description=self.description,
                instructions=(
                    Template(self._agent_config.system_prompt).substitute(**context)
                    if self._agent_config.system_prompt is not None and context
                    else self._agent_config.system_prompt
                ),
                output_type=response_model or str,
                tools=agent_tools,
                toolsets=agent_toolsets or None,
            )

            agent_run = AgentRun(
                id=agent_run_id or str(uuid4()),
                agent_id=self.id,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            agent_output: Any = None
            runtime_error: Exception | None = None

            snapshot = agent_run.model_copy(deep=True)
            try:
                yield AgentRunEvent.START, snapshot
            except (asyncio.CancelledError, GeneratorExit):
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error = "Agent stream was cancelled before completion."
                agent_run.completed_at = datetime.now()
                await agent_run_session_span(agent_run)
                raise

            try:
                async with agent.iter(
                    user_prompt=query.text if query and query.text else None,
                    message_history=agent_messages or None,
                ) as agent_pai_run:
                    async for node in agent_pai_run:
                        if isinstance(node, ModelRequestNode):
                            async with node.stream(agent_pai_run.ctx) as stream:
                                async for event in stream:
                                    delta_text = None
                                    if isinstance(event, PartStartEvent) and isinstance(
                                        event.part, TextPart
                                    ):
                                        delta_text = event.part.content
                                    elif isinstance(
                                        event, PartDeltaEvent
                                    ) and isinstance(event.delta, TextPartDelta):
                                        delta_text = event.delta.content_delta

                                    if delta_text:
                                        agent_run.delta = AgentRunContent(
                                            text=delta_text
                                        )
                                        snapshot = agent_run.model_copy(deep=True)
                                        yield AgentRunEvent.STREAM, snapshot

                        elif isinstance(node, CallToolsNode):
                            async with node.stream(agent_pai_run.ctx) as stream:
                                async for event in stream:
                                    if isinstance(event, FunctionToolCallEvent):
                                        part = event.part
                                        if part.tool_call_id in agent_run.tool_calls:
                                            warn(
                                                f"duplicate tool call: {part.tool_call_id}"
                                            )
                                            continue
                                        agent_run.tool_calls[part.tool_call_id] = (
                                            AgentRunToolCall(
                                                id=part.tool_call_id,
                                                tool_id=part.tool_name,
                                                tool_input=part.args_as_dict(),
                                                started_at=datetime.now(),
                                                status="pending",
                                            )
                                        )
                                        snapshot = agent_run.model_copy(deep=True)
                                        yield AgentRunEvent.TOOL, snapshot

                                    elif isinstance(event, FunctionToolResultEvent):
                                        tool_call = agent_run.tool_calls.get(
                                            event.tool_call_id
                                        )
                                        if not tool_call:
                                            warn(
                                                "Tool result received for unknown "
                                                f"tool call: {event.tool_call_id}"
                                            )
                                            continue

                                        part = event.part
                                        if isinstance(part, ToolReturnPart):
                                            tool_call.tool_result = _tool_result_value(
                                                part
                                            )
                                            if part.outcome == "failed":
                                                tool_call.status = "error"
                                                tool_call.error = _tool_error_value(
                                                    part
                                                )
                                            else:
                                                tool_call.status = "success"
                                        else:
                                            tool_call.status = "error"
                                            tool_call.error = _tool_error_value(part)
                                        tool_call.completed_at = datetime.now()
                                        snapshot = agent_run.model_copy(deep=True)
                                        yield AgentRunEvent.TOOL, snapshot

                    if agent_pai_run.result is None:
                        raise RuntimeError(
                            "Pydantic AI agent completed without a result"
                        )
                    agent_output = agent_pai_run.result.output
            except (asyncio.CancelledError, GeneratorExit):
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error = "Agent stream was cancelled before completion."
                agent_run.completed_at = datetime.now()
                await agent_run_session_span(agent_run)
                raise
            except Exception as e:
                runtime_error = e

            agent_run.delta = None
            if runtime_error is None:
                try:
                    if response_model:
                        if not isinstance(agent_output, response_model):
                            raise TypeError(
                                "Expected structured output "
                                f"{response_model.__name__}, got {type(agent_output)}"
                            )
                        structured_output = agent_output.model_dump(mode="json")
                    else:
                        structured_output = None

                    agent_run.reply = AgentRunContent(
                        text=_as_text(agent_output),
                        structured=structured_output,
                    )
                except Exception as e:
                    runtime_error = e

            agent_run.completed_at = datetime.now()
            if runtime_error is not None:
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error = f"Agent execution failed: {runtime_error}"
            else:
                agent_run.status = AgentRunStatus.COMPLETED

            await agent_run_session_span(agent_run)

            if runtime_error is not None:
                snapshot = agent_run.model_copy(deep=True)
                yield AgentRunEvent.FINISH, snapshot
                raise runtime_error

            snapshot = agent_run.model_copy(deep=True)
            yield AgentRunEvent.UPDATE, snapshot
            snapshot = agent_run.model_copy(deep=True)
            yield AgentRunEvent.FINISH, snapshot

    async def run_async(
        self,
        query: str | AgentRunContent = "",
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        agent_run_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
        skill_ids: List[str] | None = None,
        response_model: Type[BaseModel] | None = None,
        context: dict[str, Any] | None = None,
        event_callback: Callable[[AgentRunEvent, AgentRun], None] = lambda e, r: None,
        **kwargs,  # ignore additional kwargs
    ) -> BaseModel:
        """Execute the agent and return its final domain output."""
        response_model = (
            response_model
            if response_model is not None
            else self._agent_config.response_model
        )
        final_run: AgentRun | None = None

        async for event, agent_run in self.stream_async(
            query=query,
            agent_run_repository=agent_run_repository,
            agent_run_session_id=agent_run_session_id,
            agent_run_id=agent_run_id,
            tool_retriever=tool_retriever,
            tool_ids=tool_ids,
            skill_retriever=skill_retriever,
            skill_ids=skill_ids,
            response_model=response_model,
            context=context,
            **kwargs,
        ):
            event_callback(event, agent_run)
            final_run = agent_run

        if final_run is None or not final_run.reply:
            return AgentRunContent(text="")

        if response_model and final_run.reply.structured:
            return response_model.model_validate(final_run.reply.structured)

        return final_run.reply


class PydanticAIAgentBackend(AgentBackend):
    """Agent backend for Pydantic AI."""

    async def create_agent_async(
        self,
        model_backend: ModelBackend,
        model_config_repository: ModelConfigRepository,
        agent_config: AgentConfig,
    ) -> AgentRunnable:
        """Create an agent instance from an AgentConfig."""
        agent_model = await create_model_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            model_config_id=agent_config.model_id,
        )
        if not agent_model:
            raise RuntimeError(f"Model not found: {agent_config.model_id}")

        agent_model = agent_model.get_underlying()
        if not isinstance(agent_model, PydanticAIModelUnderlying):
            raise RuntimeError(
                f"Expected PydanticAIModelUnderlying, got {type(agent_model)}"
            )
        return PydanticAIAgentRunnable(agent_config, agent_model)
