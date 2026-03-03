from datetime import datetime
from typing import Callable, List, Type

from langchain.agents import create_agent as LangchainAgentUnderlying  # noqa
from langchain_core.language_models import BaseChatModel as LangchainModelUnderlying
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from pydantic import BaseModel

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


async def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    agent_query: AgentRunContent | None = None,
) -> List[BaseMessage]:
    agent_messages = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = await agent_run_repository.list_agent_runs_async(
            agent_run_session_id
        )
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


class LangchainAgentRunnable(AgentRunnable):
    """LangChain agent runnable."""

    def __init__(
        self,
        agent_config: AgentConfig,
        agent_model: LangchainModelUnderlying,
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
        tool_verifier: AgentRunnable | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
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
            tool_verifier: Optional agent for tool selection verification
            tool_retriever: Tool retrieval system for semantic tool search
            tool_ids: Runtime tool IDs (merged with config.tool_ids via set union)
            skill_retriever: Optional skill retriever for dynamic tool injection
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

        agent_messages = await _list_messages(
            agent_run_repository,
            agent_run_session_id,
            query,
        )

        agent_tool_ids = set(tool_ids) if tool_ids else set()
        agent_tool_ids.update(self._agent_config.tool_ids or [])

        async with (
            AgentRunToolSpan(
                tool_verifier=tool_verifier,
                tool_retriever=tool_retriever,
                tool_ids=list(agent_tool_ids),
                tool_query=query,
            ) as tools_expanded,
            AgentRunSessionSpan(
                agent_run_repository,
                agent_run_session_id,
                self.id,
            ) as agent_run_session_span,
        ):
            agent_tools = [t.get_underlying() for t in tools_expanded]
            agent = LangchainAgentUnderlying(
                self._agent_model,
                agent_tools,
                name=self.id,
                system_prompt=self._agent_config.system_prompt,
                response_format=response_model,
            )
            agent_run = AgentRun(
                agent_id=self.id,
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
                        agent_run.delta = None

                    elif mode == "messages":
                        msg, _ = event_data

                        if isinstance(msg, AIMessageChunk):
                            event = AgentRunEvent.STREAM
                            # delta contains delta message (incremental chunk), not accumulated text
                            agent_run.delta = AgentRunContent(text=msg.content)

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
                        await agent_run_session_span(agent_run)

                agent_run.status = AgentRunStatus.COMPLETED

            except Exception as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                agent = LangchainAgentUnderlying(
                    self._agent_model,
                    agent_tools,
                    name=self.id,
                    system_prompt=self._agent_config.system_prompt,
                    response_format=response_model,
                )
                outputs = await agent.ainvoke(
                    agent.InputType(messages=[HumanMessage(content=error_msg)])
                )

                agent_run.status = AgentRunStatus.FAILED

            finally:
                agent_run.completed_at = datetime.now()

                # Ensure reply is set and FINISH event is called even if an exception occurred
                try:
                    # Extract structured response if available
                    agent_run_reply_structured = None
                    if "structured_response" in outputs:
                        structured_output = outputs["structured_response"]
                        if isinstance(structured_output, BaseModel):
                            agent_run_reply_structured = structured_output

                    # Extract text content from messages
                    if "messages" in outputs:
                        output = outputs["messages"][-1]
                        if isinstance(output, BaseMessage):
                            agent_run.reply = AgentRunContent(
                                text=output.content,
                                structured=(
                                    agent_run_reply_structured.model_dump(mode="json")
                                    if agent_run_reply_structured
                                    else None
                                ),
                            )
                        else:
                            agent_run.error = (
                                f"Expected BaseMessage, got {type(output)}"
                            )
                            agent_run.status = AgentRunStatus.FAILED
                    else:
                        agent_run.error = f"Expected messages in outputs, got {outputs}"
                        agent_run.status = AgentRunStatus.FAILED
                except Exception as e:
                    agent_run.error = f"Error processing outputs: {str(e)}"
                    agent_run.status = AgentRunStatus.FAILED

                event_callback(AgentRunEvent.FINISH, agent_run)

                # Save the final agent run state to the repository
                await agent_run_session_span(agent_run)

            # Return structured output if available, otherwise return reply
            if not agent_run.reply:
                return AgentRunContent(text="")

            return (
                agent_run_reply_structured
                if agent_run_reply_structured
                else agent_run.reply
            )


class LangchainAgentBackend(AgentBackend):
    """Langchain agent backend"""

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
        if not isinstance(agent_model, LangchainModelUnderlying):
            raise RuntimeError(
                f"Expected LangchainModelUnderlying, got {type(agent_model)}"
            )
        return LangchainAgentRunnable(agent_config, agent_model)
