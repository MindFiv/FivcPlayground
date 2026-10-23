"""Pipecat agent backend and transport-backed runtime."""

import asyncio
import json
from datetime import datetime
from string import Template
from typing import Any, List, Type
from uuid import uuid4

from pydantic import BaseModel

from fivcplayground.agents import (
    AgentBackend,
    AgentConfig,
    AgentRun,
    AgentRunContent,
    AgentRunnable,
    AgentRunRepository,
    AgentRunSessionSpan,
    AgentRunStatus,
    AgentRunToolSpan,
    AgentRunSkillSpan,
)
from fivcplayground.backends.pipecat.transports import StdioTransport
from fivcplayground.models import ModelBackend, ModelConfigRepository
from fivcplayground.skills import SkillRetriever
from fivcplayground.tools import ToolRetriever
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService
from pipecat.transports.base_transport import BaseTransport
from pipecat.turns.user_start import TranscriptionUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.workers.runner import WorkerRunner


async def _list_messages(
    agent_run_repository: AgentRunRepository | None,
    agent_run_session_id: str | None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if not agent_run_repository or not agent_run_session_id:
        return messages

    def content_text(content: AgentRunContent) -> str:
        if content.text is not None:
            return str(content.text)
        if content.structured is not None:
            return json.dumps(content.structured, ensure_ascii=False)
        return ""

    runs = await agent_run_repository.list_agent_runs_async(agent_run_session_id)
    for run in runs:
        if run.query:
            messages.append({"role": "user", "content": content_text(run.query)})
        if run.reply:
            messages.append({"role": "assistant", "content": content_text(run.reply)})
    return messages


class _PipecatRunSession:
    """Persist AgentRun turns from aggregator turn events."""

    def __init__(self, agent_id: str, session_span: AgentRunSessionSpan):
        self.agent_id = agent_id
        self.session_span = session_span
        self.current: AgentRun | None = None
        self.last: AgentRun | None = None

    async def on_user_turn(self, content: str):
        self.current = AgentRun(
            id=str(uuid4()),
            agent_id=self.agent_id,
            status=AgentRunStatus.EXECUTING,
            query=AgentRunContent(text=content),
            started_at=datetime.now(),
        )
        await self.session_span(self.current)

    async def on_assistant_turn(self, content: str | None):
        if not self.current:
            return
        if content:
            self.current.reply = AgentRunContent(text=content)
        self.current.status = AgentRunStatus.COMPLETED
        self.current.completed_at = datetime.now()
        await self.session_span(self.current)
        self.last = self.current
        self.current = None

    async def fail_current(self, error: str):
        if not self.current or self.current.status != AgentRunStatus.EXECUTING:
            return
        self.current.status = AgentRunStatus.FAILED
        self.current.error = error
        self.current.completed_at = datetime.now()
        await self.session_span(self.current)
        self.last = self.current
        self.current = None


class PipecatAgentRunnable(AgentRunnable):
    """Agent runnable backed by a Pipecat transport pipeline."""

    def __init__(self, agent_config: AgentConfig, model: Any):
        self._agent_config = agent_config
        self._agent_model = model
        self._lock = asyncio.Lock()

    @property
    def id(self) -> str:
        return self._agent_config.id

    @property
    def name(self) -> str:
        return self._agent_config.name

    @property
    def description(self) -> str:
        return self._agent_config.description

    def stream_async(self, **kwargs):
        """Pipecat runs are reduction-oriented; streaming is not supported."""
        raise NotImplementedError(f"{type(self).__name__} supports run_async only")

    async def run_async(
        self,
        transport: BaseTransport | None = None,
        stt: STTService | None = None,
        tts: TTSService | None = None,
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        agent_run_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
        skill_ids: List[str] | None = None,
        response_model: Type[BaseModel] | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> BaseModel:
        """Run a transport-backed pipeline until the session ends."""
        if transport is None:
            transport = StdioTransport()
            stt = None
            tts = None
        async with self._lock:
            async with (
                AgentRunToolSpan(
                    tool_retriever=tool_retriever,
                    tool_ids=list(
                        set((tool_ids or []) + (self._agent_config.tool_ids or []))
                    ),
                    context=context,
                ) as tool_span,
                AgentRunSkillSpan(
                    skill_retriever=skill_retriever,
                    skill_ids=list(
                        set((skill_ids or []) + (self._agent_config.skill_ids or []))
                    ),
                ) as skill_span,
                AgentRunSessionSpan(
                    agent_run_repository,
                    agent_run_session_id,
                    self.id,
                ) as session_span,
            ):
                session = _PipecatRunSession(self.id, session_span)
                tools = [tool.get_underlying() for tool in tool_span.tools]
                await skill_span.register_skills_async(
                    agent_tool_span=tool_span,
                    agent_tool_register=lambda tool: tools.append(
                        tool.get_underlying()
                    ),
                )

                if response_model is None:
                    response_model = self._agent_config.response_model
                agent_output_structured: dict[str, Any] = {}
                if response_model:
                    response_schema = response_model.model_json_schema()
                    response_schema.pop("title", None)

                    async def generate_structured_output(params: FunctionCallParams):
                        parsed = response_model.model_validate(dict(params.arguments))
                        agent_output_structured.clear()
                        agent_output_structured.update(parsed.model_dump(mode="json"))
                        await params.result_callback("Structured output captured.")

                    tools.append(
                        FunctionSchema(
                            name="generate_structured_output",
                            description=(
                                "Use this tool to provide the final structured "
                                "response. Arguments must match the requested "
                                "response schema."
                            ),
                            properties=dict(response_schema.get("properties", {})),
                            required=list(response_schema.get("required", [])),
                            handler=generate_structured_output,
                        )
                    )

                system_prompt = self._agent_config.system_prompt
                if system_prompt and context:
                    system_prompt = Template(system_prompt).substitute(**context)
                if system_prompt:
                    await self._agent_model._update_settings(
                        type(self._agent_model._settings)(
                            system_instruction=system_prompt
                        )
                    )

                messages = await _list_messages(
                    agent_run_repository, agent_run_session_id
                )
                llm_context = LLMContext(messages=messages, tools=tools)
                if isinstance(transport, StdioTransport):
                    user_agg, assistant_agg = LLMContextAggregatorPair(
                        llm_context,
                        user_params=LLMUserAggregatorParams(
                            user_turn_strategies=UserTurnStrategies(
                                start=[TranscriptionUserTurnStartStrategy()],
                                stop=[
                                    ExternalUserTurnStopStrategy(
                                        wait_for_transcript=True
                                    )
                                ],
                            )
                        ),
                    )
                else:
                    user_agg, assistant_agg = LLMContextAggregatorPair(llm_context)

                processors: list[Any] = [transport.input()]
                if stt is not None:
                    processors.append(stt)
                processors.append(user_agg)
                processors.append(self._agent_model)
                if tts is not None:
                    processors.append(tts)
                processors.extend([transport.output(), assistant_agg])

                extra = self._agent_config.extra or {}
                run_name = f"{self.id}:{agent_run_id or uuid4()}"
                worker = PipelineWorker(
                    Pipeline(processors=processors),
                    enable_rtvi=False,
                    params=PipelineParams.model_validate(
                        extra.get("pipeline_params") or {}
                    ),
                    idle_timeout_secs=extra.get("idle_timeout_secs"),
                    name=run_name,
                )
                runner = WorkerRunner(handle_sigint=False, name=run_name)

                @user_agg.event_handler("on_user_turn_stopped")
                async def on_user_turn_stopped(aggregator, strategy, message):
                    if message.content:
                        await session.on_user_turn(str(message.content))

                @assistant_agg.event_handler("on_assistant_turn_stopped")
                async def on_assistant_turn_stopped(aggregator, message):
                    await session.on_assistant_turn(message.content)

                @transport.event_handler("on_client_disconnected")
                async def on_client_disconnected(disconnected_transport, client):
                    await runner.cancel()

                try:
                    await runner.add_workers(worker)
                    await runner.run()
                except (asyncio.CancelledError, GeneratorExit):
                    await session.fail_current(
                        "Agent run was cancelled before completion."
                    )
                    raise
                except Exception as e:
                    await session.fail_current(str(e))
                    raise

                final_run = session.last
                if final_run and agent_output_structured:
                    final_run.reply = AgentRunContent(
                        structured=agent_output_structured
                    )
                    await session_span(final_run)

                if final_run is None or not final_run.reply:
                    return AgentRunContent(text="")

                if response_model and final_run.reply.structured:
                    return response_model.model_validate(final_run.reply.structured)

                return final_run.reply


class PipecatAgentBackend(AgentBackend):
    """Create Pipecat agents from model and agent configuration."""

    async def create_agent_async(
        self,
        model_backend: ModelBackend,
        model_config_repository: ModelConfigRepository,
        agent_config: AgentConfig,
    ) -> AgentRunnable:
        from fivcplayground.models import create_model_async

        model = await create_model_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            model_config_id=agent_config.model_id,
        )
        return PipecatAgentRunnable(agent_config, model.get_underlying())
