import re
from datetime import datetime
from typing import Any, Callable, List, Type, cast
from uuid import uuid4
from warnings import warn

from pydantic import BaseModel
from strands.agent import (
    Agent as StrandsAgentUnderlying,
    AgentResult as StrandsAgentResult,
    SlidingWindowConversationManager,
)
from strands import (
    AgentSkills as StrandsSkillsPlugin,
)
from strands.models import Model as StrandsModelUnderlying
from strands.tools import PythonAgentTool
from strands.types.content import ContentBlock, Message
from strands.types.tools import ToolResult, ToolSpec, ToolUse

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


_JSON_FENCE_PATTERN = re.compile(
    r"(?:```|''')json\s*(?P<json>.*?)(?:```|''')",
    re.IGNORECASE | re.DOTALL,
)


def _to_content_blocks(content: AgentRunContent) -> list[ContentBlock]:
    """Convert AgentRunContent to list of ContentBlock."""
    blocks = []
    if content.text:
        blocks.append(ContentBlock(text=content.text))

    # TODO: Uncomment and wire up when image input is supported by the backend.
    # The new tuple schema is (mime_type, base64_content), e.g. ("image/png", "<base64>").
    # for fmt, content_data in (content.images or []):
    #     blocks.append(ContentBlock(image={
    #         "format": fmt.split("/")[-1],   # e.g. "image/png" -> "png"
    #         "source": {"bytes": base64.b64decode(content_data)},
    #     }))

    return blocks


async def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    agent_query: AgentRunContent | None = None,
) -> List[Message]:
    """List all messages for a specific session."""
    agent_messages = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = await agent_run_repository.list_agent_runs_async(
            agent_run_session_id
        )
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
        """
        Execute agent asynchronously with streaming support.

        Args:
            query: User query string or AgentRunContent object
            agent_run_repository: Repository for persisting agent runs
            agent_run_session_id: Session ID for conversation context
            agent_run_id: Optional explicit AgentRun ID; auto-generated UUID if omitted
            tool_retriever: Tool retrieval system for semantic tool search
            tool_ids: Runtime tool IDs (merged with config.tool_ids via set union)
            skill_retriever: Optional skill retriever for dynamic tool injection
            skill_ids: Runtime skill IDs (merged with config.skill_ids via set union)
            response_model: Structured output model (overrides config)
            context: Runtime context passed to class tool constructors
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

        agent_messages = await _list_messages(
            agent_run_repository,
            agent_run_session_id,
            query,
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
            agent_tools = [t.get_underlying() for t in agent_tool_span.tools]
            agent_output_structured: dict[str, Any] = {}
            if response_model:
                tool_name = "generate_structured_output"
                response_schema = response_model.model_json_schema()
                response_schema.pop("title", None)

                def generate_structured_output(
                    tool_use: ToolUse, **kwargs
                ) -> ToolResult:
                    """
                    generate structured output from response object
                    """
                    resp = response_model.model_validate(tool_use.get("input", {}))
                    agent_output_structured.clear()
                    agent_output_structured.update(resp.model_dump(mode="json"))
                    return ToolResult(
                        toolUseId=tool_use.get("toolUseId", tool_name),
                        status="success",
                        content=[{"text": "Structured output captured."}],
                    )

                agent_tools.append(
                    PythonAgentTool(
                        tool_name,
                        ToolSpec(
                            name=tool_name,
                            description=(
                                "Use this tool to provide the final structured "
                                "response. Arguments must match the requested "
                                "response schema."
                            ),
                            inputSchema={"json": response_schema},
                        ),
                        generate_structured_output,
                    )
                )

            agent_skill_plugin = (
                StrandsSkillsPlugin(
                    skills=agent_skill_span.get_skill_paths(),
                )
                if agent_skill_span.get_skill_paths()
                else None
            )
            agent = StrandsAgentUnderlying(
                name=self.id,
                model=self._agent_model,
                tools=agent_tools,
                system_prompt=self._agent_config.system_prompt,
                conversation_manager=SlidingWindowConversationManager(window_size=20),
                plugins=[agent_skill_plugin] if agent_skill_plugin else None,
            )

            # compatible with legacy skill logic
            await agent_skill_span.register_skills_async(
                agent_tool_span=agent_tool_span,
                agent_tool_register=lambda t: agent.tool_registry.register_dynamic_tool(
                    t.get_underlying()
                ),
            )

            # Create agent run
            agent_run = AgentRun(
                id=agent_run_id or str(uuid4()),
                agent_id=self.id,
                status=AgentRunStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            agent_output = None
            event_callback(AgentRunEvent.START, agent_run)

            try:
                async for event_data in agent.stream_async(
                    prompt=agent_messages,
                ):
                    event = AgentRunEvent.START
                    if "result" in event_data:
                        agent_output = event_data["result"]

                    elif "data" in event_data:
                        event = AgentRunEvent.STREAM
                        # delta contains delta message (incremental chunk), not accumulated text
                        agent_run.delta = AgentRunContent(text=event_data["data"])

                    elif "message" in event_data:
                        event = AgentRunEvent.UPDATE
                        agent_run.delta = None

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
                        await agent_run_session_span(agent_run)

                agent_run.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                agent_output = await agent.invoke_async(prompt=error_msg)

                agent_run.status = AgentRunStatus.FAILED

            finally:
                agent_run.completed_at = datetime.now()

                # Ensure reply is set and FINISH event is called even if an exception occurred
                agent_run_reply_structured = None
                parse_error = None
                if isinstance(agent_output, StrandsAgentResult):
                    agent_reply = str(agent_output)
                    if response_model:
                        try:
                            if agent_output_structured:
                                agent_run_reply_structured = response_model(
                                    **agent_output_structured
                                )
                            else:
                                parse_errors = []
                                try:
                                    agent_run_reply_structured = (
                                        response_model.model_validate_json(agent_reply)
                                    )
                                except ValueError as e:
                                    parse_errors.append(f"whole reply: {e}")

                                if not agent_run_reply_structured:
                                    for match in _JSON_FENCE_PATTERN.finditer(
                                        agent_reply
                                    ):
                                        try:
                                            agent_run_reply_structured = (
                                                response_model.model_validate_json(
                                                    match.group("json").strip()
                                                )
                                            )
                                            break
                                        except ValueError as e:
                                            parse_errors.append(f"fenced json: {e}")

                                if not agent_run_reply_structured:
                                    details = (
                                        "; ".join(parse_errors)
                                        if parse_errors
                                        else "no JSON content found"
                                    )
                                    raise ValueError(
                                        "Failed to parse structured output from "
                                        f"agent reply: {details}"
                                    )

                                agent_output_structured.update(
                                    agent_run_reply_structured.model_dump(mode="json")
                                )
                        except ValueError as e:
                            parse_error = e
                            agent_run.error = str(e)
                            agent_run.status = AgentRunStatus.FAILED

                    agent_run.reply = AgentRunContent(
                        text=agent_reply,
                        structured=agent_output_structured or None,
                    )
                else:
                    agent_run.error = f"Expected AgentResult, got {type(agent_output)}"
                    agent_run.status = AgentRunStatus.FAILED

                event_callback(AgentRunEvent.FINISH, agent_run)

                # Save the final agent run state to the repository
                await agent_run_session_span(agent_run)

                if parse_error:
                    raise parse_error

            if not agent_run.reply:
                return AgentRunContent(text="")

            return (
                agent_run_reply_structured
                if agent_run_reply_structured
                else agent_run.reply
            )


class StrandsAgentBackend(AgentBackend):
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
        if not isinstance(agent_model, StrandsModelUnderlying):
            raise RuntimeError(
                f"Expected StrandsModelUnderlying, got {type(agent_model)}"
            )
        return StrandsAgentRunnable(agent_config, agent_model)
