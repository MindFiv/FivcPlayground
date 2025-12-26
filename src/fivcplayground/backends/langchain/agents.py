import asyncio
from datetime import datetime
from typing import List, Type, Callable

from langchain_core.messages import (
    HumanMessage,
    BaseMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel as LangchainModelUnderlying
from langchain.agents import create_agent as LangchainAgentUnderlying

from pydantic import BaseModel

from fivcplayground.agents import (
    AgentConfig,
    AgentRunEvent,
    AgentRunStatus,
    AgentRunContent,
    AgentRunToolCall,
    AgentRun,
    AgentRunnable,
    AgentRunRepository,
    AgentRunSessionSpan,
    AgentRunToolSpan,
    AgentBackend,
)
from fivcplayground.models import Model
from fivcplayground.tools import ToolRetriever


def _list_messages(
    agent_run_repository: AgentRunRepository | None = None,
    agent_run_session_id: str | None = None,
    agent_query: AgentRunContent | None = None,
) -> List[BaseMessage]:
    agent_messages = []
    if agent_run_repository and agent_run_session_id:
        agent_runs = agent_run_repository.list_agent_runs(agent_run_session_id)
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
                        agent_run.streaming_text = ""

                    elif mode == "messages":
                        msg, _ = event_data

                        if isinstance(msg, AIMessageChunk):
                            event = AgentRunEvent.STREAM
                            agent_run.streaming_text += msg.content

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
                        agent_run_session_span(agent_run)

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
                    if "messages" in outputs:
                        output = outputs["messages"][-1]
                        if isinstance(output, BaseMessage):
                            agent_run.reply = AgentRunContent(text=output.content)
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
                agent_run_session_span(agent_run)

            # Return structured output if available, otherwise return reply
            if "structured_response" in outputs:
                output = outputs["structured_response"]
                if isinstance(output, BaseModel):
                    return output

            return agent_run.reply if agent_run.reply else AgentRunContent(text="")


class LangchainAgentBackend(AgentBackend):
    """Langchain agent backend"""

    def create_agent(
        self,
        agent_model: Model,
        agent_config: AgentConfig,
    ) -> AgentRunnable:
        """Create an agent instance from an AgentConfig."""
        agent_model = agent_model.get_underlying()
        if not isinstance(agent_model, LangchainModelUnderlying):
            raise RuntimeError(
                f"Expected LangchainModelUnderlying, got {type(agent_model)}"
            )
        return LangchainAgentRunnable(agent_config, agent_model)
