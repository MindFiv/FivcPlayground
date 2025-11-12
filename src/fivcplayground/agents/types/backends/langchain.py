"""
Runnable wrapper for LangChain agents.

This module provides the AgentsRunnable class, which wraps LangChain's native
agent creation functions to provide a consistent Runnable interface for FivcPlayground
agents. It handles both synchronous and asynchronous invocation with proper message
formatting and output extraction.

Core Classes:
    - AgentsRunnable: Runnable wrapper for LangChain agents

Features:
    - Synchronous and asynchronous execution
    - Automatic message history management
    - Structured response support via response_model
    - Callback handler integration for monitoring
    - Multi-turn conversation support

Return Types:
    - If response_model is provided: Returns Pydantic model instance
    - If response_model is None: Returns string content from agent response

Example:
    >>> from fivcplayground.agents.types import AgentsRunnable
    >>> from langchain_openai import ChatOpenAI
    >>>
    >>> # Create a model
    >>> model = ChatOpenAI(model="gpt-4o-mini")
    >>>
    >>> # Create an agent
    >>> agent = AgentsRunnable(
    ...     model=model,
    ...     tools=[],
    ...     agent_name="MyAgent",
    ...     system_prompt="You are a helpful assistant"
    ... )
    >>> result = agent.run("Hello!")
    >>> print(result)  # Returns string
"""

import asyncio
from datetime import datetime
from typing import Any, List, Type, Union, Callable
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.messages import (
    HumanMessage,
    BaseMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel

from fivcplayground.agents.types.base import (
    AgentsContent,
    AgentsStatus,
    AgentsEvent,
    AgentsRuntime,
    AgentsRuntimeToolCall,
)
from fivcplayground.tools import setup_tools, Tool
from fivcplayground.utils import Runnable


class AgentsRunnable(Runnable):
    """
    Stateless runnable wrapper for LangChain agents.

    This class wraps LangChain's native agent creation functions to provide
    a consistent Runnable interface for FivcPlayground agents. It handles both
    synchronous and asynchronous invocation with proper message formatting
    and output extraction.

    The agent supports two input modes:
    - String queries: Automatically converted to HumanMessage
    - Message history: Direct list of AnyMessage objects for multi-turn conversations

    Return Types:
    - If response_model is provided: Returns Pydantic model instance
    - If response_model is None: Returns string content from agent response

    Attributes:
        _id: Unique identifier for the runnable
        _agent: The underlying LangChain agent (compiled state graph)
        _name: Agent name
        _system_prompt: System prompt for the agent
        _callback_handler: Optional callback handler for execution events
        _messages: List of messages accumulated during execution

    Example:
        >>> from fivcplayground.agents.types import AgentsRunnable
        >>> from langchain_openai import ChatOpenAI
        >>> from langchain_core.messages import HumanMessage, AIMessage
        >>>
        >>> # Create a model
        >>> model = ChatOpenAI(model="gpt-4o-mini")
        >>>
        >>> # Create an agent
        >>> agent = AgentsRunnable(
        ...     model=model,
        ...     tools=[],
        ...     agent_name="MyAgent",
        ...     system_prompt="You are a helpful assistant"
        ... )
        >>>
        >>> # Run with string query - returns string
        >>> result = agent.run("What is 2+2?")
        >>> print(result)  # "4"
        >>>
        >>> # Run with message history
        >>> messages = [
        ...     HumanMessage(content="What is 2+2?"),
        ...     AIMessage(content="2+2 equals 4"),
        ...     HumanMessage(content="What about 3+3?")
        ... ]
        >>> result = agent.run(messages)
        >>> print(result)  # "3+3 equals 6"
        >>>
        >>> # Run asynchronously
        >>> import asyncio
        >>> result = asyncio.run(agent.run_async("What is 2+2?"))
        >>> print(result)  # "4"
        >>>
        >>> # Run with structured response
        >>> from pydantic import BaseModel
        >>> class Answer(BaseModel):
        ...     value: int
        >>> agent = AgentsRunnable(
        ...     model=model,
        ...     tools=[],
        ...     response_model=Answer
        ... )
        >>> result = agent.run("What is 2+2?")
        >>> print(result.value)  # 4
    """

    def __init__(
        self,
        model: BaseChatModel | None = None,
        tools: List[Tool] | None = None,
        agent_id: str | None = None,
        agent_name: str = "Default",
        system_prompt: str | None = None,
        messages: List[AgentsRuntime] | None = None,
        response_model: Type[BaseModel] | None = None,
        callback_handler: Callable[[AgentsEvent, AgentsRuntime], None] | None = None,
        **kwargs,
    ):
        """
        Initialize AgentsRunnable.

        Args:
            model: LangChain chat model
            tools: List of LangChain tools
            agent_id: Unique identifier for the agent (auto-generated if not provided)
            agent_name: Human-readable name for the agent (default: 'Default')
            system_prompt: System prompt/instructions for the agent
            response_model: Optional Pydantic model class for structured output.
                           When provided, the agent will return instances of this model
                           instead of strings. The model is passed to create_agent as
                           response_format for automatic conversion.
            **kwargs: Additional arguments (ignored for compatibility)

        Example:
            >>> from langchain_openai import ChatOpenAI
            >>> from pydantic import BaseModel
            >>>
            >>> class MyResponse(BaseModel):
            ...     answer: str
            ...     confidence: float
            >>>
            >>> model = ChatOpenAI(model="gpt-4o-mini")
            >>> agent = AgentsRunnable(
            ...     model=model,
            ...     tools=[],
            ...     agent_name="MyAgent",
            ...     system_prompt="You are helpful",
            ...     response_model=MyResponse
            ... )
        """
        self._id = agent_id or str(uuid4())
        self._name = agent_name
        self._system_prompt = system_prompt
        self._callback_handler = callback_handler
        self._response_model = response_model
        self._model = model
        self._tools = tools
        self._messages = []

        # Convert messages to LangChain format
        for m in messages or []:
            if not m.is_completed:
                continue

            if m.query and m.query.text:
                self._messages.append(HumanMessage(content=m.query.text))

            if m.reply and m.reply.text:
                self._messages.append(AIMessage(content=m.reply.text))

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
                self._messages.append(HumanMessage(content=query.text))

        async with setup_tools(self._tools) as tools_expanded:
            agent = create_agent(
                self._model,
                tools_expanded,
                name=self._name,
                system_prompt=self._system_prompt,
                response_format=self._response_model,
            )
            runtime = AgentsRuntime(
                agent_id=self._id,
                agent_name=self._name,
                status=AgentsStatus.EXECUTING,
                query=query or None,
                started_at=datetime.now(),
            )
            outputs = {}
            if self._callback_handler:
                self._callback_handler(AgentsEvent.START, runtime)

            try:
                async for mode, event_data in agent.astream(
                    agent.InputType(messages=self._messages),
                    stream_mode=["messages", "values", "updates"],
                ):
                    event = AgentsEvent.START

                    if mode == "values":
                        outputs = event_data

                    elif mode == "updates":
                        event = AgentsEvent.UPDATE
                        runtime.streaming_text = ""

                    elif mode == "messages":
                        msg, _ = event_data

                        if isinstance(msg, AIMessageChunk):
                            event = AgentsEvent.STREAM
                            runtime.streaming_text += msg.text

                        elif isinstance(msg, ToolMessage):
                            event = AgentsEvent.TOOL
                            tool_call = AgentsRuntimeToolCall(
                                tool_use_id=msg.tool_call_id,
                                tool_name=msg.name,
                                # tool_input=msg.input,
                                tool_result=msg.content,
                                started_at=datetime.now(),
                                completed_at=datetime.now(),
                                status=msg.status,
                            )
                            runtime.tool_calls[tool_call.tool_use_id] = tool_call

                    if self._callback_handler and event != AgentsEvent.START:
                        self._callback_handler(event, runtime)

                runtime.status = AgentsStatus.COMPLETED

            except GraphRecursionError as e:
                error_msg = f"Kindly notify the error we've encountered now: {str(e)}"
                outputs = await agent.ainvoke(
                    agent.InputType(messages=[HumanMessage(content=error_msg)])
                )
                runtime.status = AgentsStatus.FAILED
            finally:
                runtime.completed_at = datetime.now()

            if "messages" not in outputs:
                raise ValueError(f"Expected messages in outputs, got {outputs}")

            output = outputs["messages"][-1]
            if not isinstance(output, BaseMessage):
                raise ValueError(
                    f"Expected structured_response to be BaseMessage, got {type(output)}"
                )

            self._messages.append(output)

            output = AgentsContent(text=output.text)
            runtime.reply = output

            if self._callback_handler:
                self._callback_handler(AgentsEvent.FINISH, runtime)

            if "structured_response" in outputs:
                output = outputs["structured_response"]
                if not isinstance(output, BaseModel):
                    raise ValueError(
                        f"Expected structured_response to be BaseModel, got {type(output)}"
                    )

            return output
