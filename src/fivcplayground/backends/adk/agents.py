from datetime import datetime
from typing import Callable, List, Type, Dict
from warnings import warn

from pydantic import BaseModel, ValidationError
from google.adk.agents import Agent as AdkAgentUnderlying
from google.adk.events import Event
from google.adk.models import BaseLlm as AdkModelUnderlying
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

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
)
from fivcplayground.models import (
    ModelBackend,
    ModelConfigRepository,
    create_model_async,
)
from fivcplayground.skills import SkillRetriever
from fivcplayground.tools import ToolRetriever


def _to_parts(content: AgentRunContent) -> list[Part]:
    """Convert AgentRunContent to list of Content."""
    blocks = []
    if content.text:
        blocks.append(Part(text=content.text))

    # TODO: Uncomment and wire up when image input is supported by the backend.
    # The new tuple schema is (mime_type, base64_content), e.g. ("image/png", "<base64>").
    # for fmt, content_data in (content.images or []):
    #     blocks.append(ContentBlock(image={
    #         "format": fmt.split("/")[-1],   # e.g. "image/png" -> "png"
    #         "source": {"bytes": base64.b64decode(content_data)},
    #     }))

    return blocks


def _get_content_text(content: Content) -> str:
    """Convert AgentRunContent to list of text."""
    blocks = []
    for p in content.parts:
        if p.text:
            blocks.append(p.text)

    return "".join(blocks)


async def _list_events(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    # agent_query: AgentRunContent | None = None,
) -> List[Event]:
    """List all messages for a specific session."""
    agent_events = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = await agent_run_repository.list_agent_runs_async(
            agent_run_session_id
        )
        for m in agent_runs:
            if not m.is_completed:
                continue

            if m.query:
                agent_events.append(
                    Event(author="user", content=Content(parts=_to_parts(m.query))),
                )

            if m.reply:
                agent_events.append(
                    Event(author=m.agent_id, content=Content(parts=_to_parts(m.reply)))
                )

    # if agent_query:
    #     agent_events.append(
    #         Event(
    #             author="user",
    #             content=Content(parts=_to_parts(agent_query))
    #         )
    #     )
    return agent_events


class AdkAgentRunnable(AgentRunnable):
    def __init__(
        self,
        agent_config: AgentConfig,
        agent_model: AdkModelUnderlying,
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

    async def run_async(
        self,
        query: str | AgentRunContent = "",
        agent_run_repository: AgentRunRepository | None = None,
        agent_run_session_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
        skill_ids: List[str] | None = None,
        response_model: Type[BaseModel] | None = None,
        event_callback: Callable[[AgentRunEvent, AgentRun], None] = lambda e, r: None,
        **kwargs,  # ignore additional kwargs
    ) -> BaseModel:
        """
        Execute agent asynchronously with streaming support.

        Args:
            query: User query string or AgentRunContent object
            agent_run_repository: Repository for persisting agent runs
            agent_run_session_id: Session ID for conversation context
            tool_retriever: Tool retrieval system for semantic tool search
            tool_ids: Runtime tool IDs (merged with config.tool_ids via set union)
            skill_retriever: Optional skill retriever for dynamic tool injection
            skill_ids: Runtime skill IDs (merged with config.skill_ids via set union)
            response_model: Structured output model (overrides config)
            event_callback: Callback for execution events
            **kwargs: Additional arguments (ignored)

        Returns:
            Structured output model instance or AgentRunContent

        Notes:
            - tool_ids are merged with config.tool_ids using set union
        """
        response_model = (
            response_model
            if response_model is not None
            else self._agent_config.response_model
        )

        if query and not isinstance(query, AgentRunContent):
            query = AgentRunContent(text=str(query))

        adk_session_service = InMemorySessionService()
        adk_session_id = agent_run_session_id or "tmp-session"
        adk_session = await adk_session_service.create_session(
            app_name="fivcplayground",
            user_id="tmp-user",
            session_id=adk_session_id,
        )

        adk_session.events.extend(
            await _list_events(
                agent_run_repository,
                adk_session_id,
                # query,
            )
        )

        agent_tool_ids = set(tool_ids) if tool_ids else set()
        agent_tool_ids.update(self._agent_config.tool_ids or [])

        agent_skill_ids = set(skill_ids) if skill_ids else set()
        agent_skill_ids.update(self._agent_config.skill_ids or [])

        # Resolve registered skill IDs; if a SkillConfig has `path`, also route it
        # through StrandsSkillsPlugin while keeping the ID exposed via SkillRetriever.
        agent_skill_locations = []
        agent_skill_legacy_ids = []

        if skill_retriever and agent_skill_ids:
            for sid in agent_skill_ids:
                skill = await skill_retriever.get_skill_async(sid)
                if not skill:
                    continue

                if skill.path:
                    agent_skill_locations.append(skill.path)
                else:
                    agent_skill_legacy_ids.append(sid)

        agent_output = None
        agent_output_structured = None

        async with (
            AgentRunToolSpan(
                tool_retriever=tool_retriever,
                tool_ids=list(agent_tool_ids),
            ) as agent_tool_span,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self.id,
            ) as agent_run_session_span,
        ):
            agent_tools = [t.get_underlying() for t in agent_tool_span.tools]
            agent = Runner(
                app_name="fivcplayground",
                session_service=adk_session_service,
                agent=AdkAgentUnderlying(
                    name=self.id,
                    model=self._agent_model,
                    tools=agent_tools,
                    instruction=self._agent_config.system_prompt,
                ),
            )
            # Create agent run
            agent_run = AgentRun(
                agent_id=self.id,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            agent_calls: Dict[str, AgentRunToolCall] = {}
            event_callback(AgentRunEvent.START, agent_run)

            try:
                async for event_data in agent.run_async(
                    user_id="tmp-user",
                    session_id=adk_session_id,
                    new_message=Content(role="user", parts=_to_parts(query)),
                ):
                    event = AgentRunEvent.START
                    has_function_calls = False

                    for event_call in event_data.get_function_calls():
                        if event_call.id in agent_calls:
                            warn(f"duplicate call: {event_call.id}")
                            continue

                        agent_calls[event_call.id] = AgentRunToolCall(
                            id=event_call.id,
                            tool_id=event_call.name,
                            tool_input=event_call.args or {},
                            started_at=datetime.now(),
                            status="pending",
                        )
                        has_function_calls = True

                    for event_call in event_data.get_function_responses():
                        if event_call.id not in agent_calls:
                            warn(
                                f"Tool response received for unknown tool call: {event_call.id}",
                            )
                            continue

                        agent_call = agent_calls[event_call.id]
                        agent_call.tool_result = event_call.response
                        agent_call.completed_at = datetime.now()
                        agent_call.status = "success"

                    if has_function_calls:
                        event = AgentRunEvent.TOOL

                    agent_run.tool_calls = dict(agent_calls)

                    # get delta stream
                    agent_delta = _get_content_text(event_data.content)
                    if agent_delta:
                        event = AgentRunEvent.STREAM
                        agent_run.delta = AgentRunContent(text=agent_delta)

                    if event_data.is_final_response():
                        agent_output = event_data.content
                        agent_calls.clear()
                        # For final response, always emit UPDATE event
                        event = AgentRunEvent.UPDATE

                    if event != AgentRunEvent.START:
                        event_callback(event, agent_run)

                    if event == AgentRunEvent.UPDATE:
                        await agent_run_session_span(agent_run)

                agent_run.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"we've encountered unexpected errors now: {str(e)}"
                agent_run.reply = AgentRunContent(text=error_msg)
                agent_run.error = error_msg
                agent_run.status = AgentRunStatus.FAILED

            finally:
                agent_run.completed_at = datetime.now()

                agent_reply = _get_content_text(agent_output) if agent_output else ""

                # Fallback: if the model returned JSON text instead of calling the
                # structured-output tool, try to parse it directly.
                if response_model and not agent_output_structured and agent_reply:
                    try:
                        agent_output_structured = response_model.model_validate_json(
                            agent_reply
                        )
                    except (ValidationError, ValueError):
                        agent_output_structured = None

                agent_run.reply = AgentRunContent(
                    text=agent_reply,
                    structured=(
                        agent_output_structured.model_dump(mode="json")
                        if agent_output_structured
                        else None
                    ),
                )

                event_callback(AgentRunEvent.FINISH, agent_run)

                await agent_run_session_span(agent_run)

            if not agent_run.reply:
                return AgentRunContent(text="")

            return (
                agent_output_structured if agent_output_structured else agent_run.reply
            )


class AdkAgentBackend(AgentBackend):
    """Agent backend for strands"""

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
        if not isinstance(agent_model, AdkModelUnderlying):
            raise RuntimeError(f"Expected AdkModelUnderlying, got {type(agent_model)}")
        return AdkAgentRunnable(agent_config, agent_model)
