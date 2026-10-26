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
from fivcplayground.backends.pipecat.metrics import LatencyProbe, VoiceLatencyTracker
from fivcplayground.backends.pipecat.transports import StdioTransport
from fivcplayground.models import ModelBackend, ModelConfigRepository
from fivcplayground.skills import SkillRetriever
from fivcplayground.speeches import SpeechRecognizer, SpeechSynthesizer
from fivcplayground.tools import ToolRetriever
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.audio.vad.vad_analyzer import VADAnalyzer
from pipecat.frames.frames import (
    ErrorFrame,
    InputAudioRawFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    UserAudioRawFrame,
    VADUserStartedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.settings import STTSettings, TTSSettings
from pipecat.services.stt_service import SegmentedSTTService
from pipecat.services.tts_service import (
    TTSService as PipecatTTSService,
    TextAggregationMode,
)
from pipecat.transports.base_transport import BaseTransport
from pipecat.turns.user_start import TranscriptionUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.utils.time import time_now_iso8601
from pipecat.utils.tracing.service_decorators import traced_stt, traced_tts
from pipecat.workers.runner import WorkerRunner

DEFAULT_STT_TTFS_P99_LATENCY = 1.0
DEFAULT_STT_TRAILING_SILENCE_SECS = 0.1


class STTService(SegmentedSTTService):
    """Wrap a ``SpeechRecognizer`` for use in a Pipecat pipeline.

    When the recognizer exposes ``begin_utterance`` / ``push_audio`` /
    ``end_utterance``, audio is streamed to ASR while the user is speaking so
    the websocket handshake overlaps with speech instead of starting after VAD
    stop.
    """

    def __init__(self, recognizer: SpeechRecognizer, **kwargs) -> None:
        option = recognizer.get_option()
        self._live = kwargs.pop(
            "live",
            all(
                callable(getattr(recognizer, name, None))
                for name in ("begin_utterance", "push_audio", "end_utterance")
            ),
        )
        self._latency_tracker: VoiceLatencyTracker | None = kwargs.pop(
            "latency_tracker", None
        )
        super().__init__(
            sample_rate=kwargs.pop("sample_rate", option.sample_rate),
            trailing_silence_secs=kwargs.pop(
                "trailing_silence_secs", DEFAULT_STT_TRAILING_SILENCE_SECS
            ),
            ttfs_p99_latency=kwargs.pop(
                "ttfs_p99_latency", DEFAULT_STT_TTFS_P99_LATENCY
            ),
            settings=STTSettings(
                model=kwargs.pop("model", recognizer.id),
                language=option.language,
            ),
            **kwargs,
        )
        self._recognizer = recognizer
        self._recognizer_entered = False
        self._live_utterance = False

    def _mark_stt_first_audio(self) -> None:
        if self._latency_tracker is not None:
            self._latency_tracker.mark_stt_first_audio()

    def _mark_stt_first_result(self) -> None:
        if self._latency_tracker is not None:
            self._latency_tracker.mark_stt_first_result()

    @property
    def recognizer(self) -> SpeechRecognizer:
        return self._recognizer

    @property
    def wants_wav_segments(self) -> bool:
        return self._recognizer.get_option().format == "wav"

    async def start(self, frame):
        await super().start(frame)
        if not self._recognizer_entered:
            await self._recognizer.__aenter__()
            self._recognizer_entered = True

    async def cleanup(self):
        if self._live_utterance and hasattr(self._recognizer, "cancel_utterance"):
            await self._recognizer.cancel_utterance()
            self._live_utterance = False
        if self._recognizer_entered:
            await self._recognizer.__aexit__(None, None, None)
            self._recognizer_entered = False
        await super().cleanup()

    @traced_stt
    async def _handle_transcription(self, transcript: str, is_final: bool):
        return None

    async def process_audio_frame(
        self, frame: InputAudioRawFrame, direction: FrameDirection
    ):
        if isinstance(frame, UserAudioRawFrame):
            self._user_id = frame.user_id
        else:
            self._user_id = ""

        if self._live_utterance:
            if frame.audio:
                self._mark_stt_first_audio()
            await self._recognizer.push_audio(frame.audio)
            return

        if frame.audio:
            self._mark_stt_first_audio()
        await super().process_audio_frame(frame, direction)

    async def _handle_user_started_speaking(self, frame: VADUserStartedSpeakingFrame):
        self._user_speaking = True
        if not self._live:
            return
        try:
            await self._recognizer.begin_utterance()
            self._live_utterance = True
            # Flush VAD pre-roll already buffered by SegmentedSTTService.
            if self._audio_buffer:
                self._mark_stt_first_audio()
                await self._recognizer.push_audio(bytes(self._audio_buffer))
                self._audio_buffer.clear()
        except Exception as e:
            self._live_utterance = False
            await self.push_error_frame(
                ErrorFrame(error=f"STT begin_utterance failed: {e}")
            )

    async def _handle_user_stopped_speaking(self, frame: VADUserStoppedSpeakingFrame):
        if not self._live or not self._live_utterance:
            await super()._handle_user_stopped_speaking(frame)
            return

        self._user_speaking = False
        self._live_utterance = False
        if not self.is_usable:
            if hasattr(self._recognizer, "cancel_utterance"):
                await self._recognizer.cancel_utterance()
            self._audio_buffer.clear()
            return

        trailing = self._trailing_silence()
        if trailing:
            await self._recognizer.push_audio(trailing)
        self._audio_buffer.clear()
        await self.process_generator(self._finalize_live_stt())

    async def _finalize_live_stt(self):
        try:
            await self.start_processing_metrics()
            async for event in self._recognizer.end_utterance():
                if event.type == "error":
                    yield ErrorFrame(error=event.message or "Speech recognition error")
                    continue
                if event.type != "final":
                    continue
                text = (event.text or "").strip()
                if not text:
                    continue
                await self._handle_transcription(text, True)
                self._mark_stt_first_result()
                yield TranscriptionFrame(text, self._user_id, time_now_iso8601())
            await self.stop_processing_metrics()
        except Exception as e:
            yield ErrorFrame(error=f"STT error: {e}")

    async def run_stt(self, audio: bytes):
        try:
            if audio:
                self._mark_stt_first_audio()
            await self.start_processing_metrics()
            async for event in self._recognizer.stream_async(audio):
                if event.type == "error":
                    yield ErrorFrame(error=event.message or "Speech recognition error")
                    continue
                if event.type != "final":
                    continue
                text = (event.text or "").strip()
                if not text:
                    continue
                await self._handle_transcription(text, True)
                self._mark_stt_first_result()
                yield TranscriptionFrame(text, self._user_id, time_now_iso8601())
            await self.stop_processing_metrics()
        except Exception as e:
            yield ErrorFrame(error=f"STT error: {e}")


class TTSService(PipecatTTSService):
    """Wrap a ``SpeechSynthesizer`` for use in a Pipecat pipeline."""

    def __init__(self, synthesizer: SpeechSynthesizer, **kwargs) -> None:
        option = synthesizer.get_option()
        self._latency_tracker: VoiceLatencyTracker | None = kwargs.pop(
            "latency_tracker", None
        )
        super().__init__(
            sample_rate=kwargs.pop("sample_rate", option.sample_rate),
            text_aggregation_mode=kwargs.pop(
                "text_aggregation_mode", TextAggregationMode.SENTENCE
            ),
            push_start_frame=True,
            push_stop_frames=True,
            settings=TTSSettings(
                model=kwargs.pop("model", synthesizer.id),
                voice=option.voice,
                language=None,
            ),
            **kwargs,
        )
        self._synthesizer = synthesizer
        self._synthesizer_entered = False

    @property
    def synthesizer(self) -> SpeechSynthesizer:
        return self._synthesizer

    def can_generate_metrics(self) -> bool:
        return True

    @property
    def _effective_sample_rate(self) -> int:
        return (
            self.sample_rate
            or self._init_sample_rate
            or self._synthesizer.get_option().sample_rate
        )

    async def start(self, frame):
        await super().start(frame)
        if not self._synthesizer_entered:
            await self._synthesizer.__aenter__()
            self._synthesizer_entered = True

    async def cleanup(self):
        if self._synthesizer_entered:
            await self._synthesizer.__aexit__(None, None, None)
            self._synthesizer_entered = False
        await super().cleanup()

    @traced_tts
    async def run_tts(self, text: str, context_id: str):
        try:
            if self._latency_tracker is not None:
                self._latency_tracker.mark_tts_first_input()
            await self.start_processing_metrics()
            async for audio in self._synthesizer.stream_async(text):
                if audio:
                    if self._latency_tracker is not None:
                        self._latency_tracker.mark_tts_first_output()
                    yield TTSAudioRawFrame(
                        audio=audio,
                        sample_rate=self._effective_sample_rate,
                        num_channels=1,
                        context_id=context_id,
                    )
            await self.stop_processing_metrics()
        except Exception as e:
            yield ErrorFrame(error=f"TTS error: {e}")


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
        stt: SpeechRecognizer | None = None,
        tts: SpeechSynthesizer | None = None,
        vad: VADAnalyzer | None = None,
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
        """Run a transport-backed pipeline until the session ends.

        For non-stdio (e.g. local mic) voice pipelines, pass ``vad`` so the
        user aggregator can emit VAD frames for segmented STT. ``stt`` /
        ``tts`` are speech abstractions wrapped into Pipecat services.
        """
        if transport is None:
            transport = StdioTransport()
            stt = None
            tts = None
        trailing_silence = kwargs.pop(
            "stt_trailing_silence_secs", DEFAULT_STT_TRAILING_SILENCE_SECS
        )
        latency_tracker: VoiceLatencyTracker | None = kwargs.pop(
            "latency_tracker", None
        )
        stt_service = (
            STTService(
                stt,
                trailing_silence_secs=trailing_silence,
                latency_tracker=latency_tracker,
            )
            if stt is not None
            else None
        )
        tts_service = (
            TTSService(tts, latency_tracker=latency_tracker)
            if tts is not None
            else None
        )
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
                elif vad is not None:
                    user_agg, assistant_agg = LLMContextAggregatorPair(
                        llm_context,
                        user_params=LLMUserAggregatorParams(
                            vad_analyzer=vad,
                        ),
                    )
                else:
                    user_agg, assistant_agg = LLMContextAggregatorPair(llm_context)

                processors: list[Any] = [transport.input()]
                if stt_service is not None:
                    processors.append(stt_service)
                processors.append(user_agg)
                if latency_tracker is not None:
                    processors.append(LatencyProbe(latency_tracker, role="llm_in"))
                processors.append(self._agent_model)
                if latency_tracker is not None:
                    processors.append(LatencyProbe(latency_tracker, role="llm_out"))
                if tts_service is not None:
                    processors.append(tts_service)
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
