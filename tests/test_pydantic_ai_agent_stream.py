from typing import Any, List
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import ModelRequest

from fivcplayground.agents.types.base import AgentConfig
from fivcplayground.backends.pydantic_ai.agents import PydanticAIAgentRunnable
from fivcplayground.backends.pydantic_ai.tools import PydanticAIToolBackend
from fivcplayground.skills.types.base import SkillConfig


class StructuredReply(BaseModel):
    answer: str
    confidence: float


def _repository():
    repository = AsyncMock()
    repository.get_agent_run_session_async = AsyncMock(return_value=None)
    repository.update_agent_run_session_async = AsyncMock()
    repository.update_agent_run_async = AsyncMock()
    repository.list_agent_runs_async = AsyncMock(return_value=[])
    return repository


def _runnable(model: Any) -> PydanticAIAgentRunnable:
    return PydanticAIAgentRunnable(
        AgentConfig(id="pai-test", model_id="test"),
        model,
    )


class _ToolRetriever:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    async def get_tool_async(self, name: str):
        return self.tools.get(name)

    async def list_tools_async(self) -> List[Any]:
        return list(self.tools.values())

    def to_tool(self, dummy: bool = False, **kwargs):
        raise AssertionError("The test should request a known tool directly")


async def _events(runnable, **kwargs):
    return [item async for item in runnable.stream_async(**kwargs)]


@pytest.mark.asyncio
async def test_current_query_is_not_duplicated_in_history():
    class MessageCountingModel(TestModel):
        async def request(self, messages, agent_info, model_settings=None):
            user_requests = [
                message for message in messages if isinstance(message, ModelRequest)
            ]
            assert len(user_requests) == 1
            assert user_requests[0].parts[0].content == "Say hello"
            return await super().request(
                messages,
                agent_info,
                model_settings=model_settings,
            )

    runnable = _runnable(
        MessageCountingModel(call_tools=[], custom_output_text="hello")
    )
    events = await _events(runnable, query="Say hello")
    assert events[-1][1].reply.text == "hello"


@pytest.mark.asyncio
async def test_text_stream_and_final_reply():
    runnable = _runnable(TestModel(call_tools=[], custom_output_text="hello"))
    events = await _events(runnable, query="Say hello")

    kinds = [event for event, _run in events]
    assert kinds[0].value == "start"
    assert kinds[-1].value == "finish"
    assert "update" in kinds
    assert any(event.value == "stream" for event in kinds)

    final_run = events[-1][1]
    assert final_run.status.value == "completed"
    assert final_run.reply.text == "hello"
    assert final_run.reply.structured is None


@pytest.mark.asyncio
async def test_function_tool_call_and_result():
    tool_backend = PydanticAIToolBackend()

    def echo(text: str) -> str:
        """Echo the provided text."""
        return f"echo:{text}"

    tool = tool_backend.create_tool(echo)
    runnable = _runnable(
        TestModel(call_tools=["echo"], custom_output_text="tool finished")
    )
    events = await _events(
        runnable,
        query="call echo",
        tool_retriever=_ToolRetriever([tool]),
        tool_ids=["echo"],
    )

    kinds = [event for event, _run in events]
    assert "tool" in kinds
    final_run = events[-1][1]
    assert final_run.tool_call_count == 1
    tool_call = next(iter(final_run.tool_calls.values()))
    assert tool_call.tool_id == "echo"
    assert tool_call.status == "success"
    assert tool_call.tool_result.startswith("echo:")
    assert final_run.reply.text == "tool finished"


@pytest.mark.asyncio
async def test_structured_output():
    runnable = _runnable(
        TestModel(
            call_tools=[],
            custom_output_args={"answer": "ready", "confidence": 0.9},
        )
    )
    result = await runnable.run_async(
        query="Return structured output",
        response_model=StructuredReply,
    )
    assert isinstance(result, StructuredReply)
    assert result.answer == "ready"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_runtime_error_persists_failed_run_and_finishes():
    repository = _repository()
    runnable = _runnable(TestModel(call_tools=["missing-tool"]))

    with pytest.raises(Exception, match="unknown tool"):
        await _events(
            runnable,
            query="trigger failure",
            agent_run_repository=repository,
            agent_run_session_id="session",
        )

    repository.update_agent_run_async.assert_called()
    saved_run = repository.update_agent_run_async.call_args.args[1]
    assert saved_run.status.value == "failed"
    assert saved_run.error


@pytest.mark.asyncio
async def test_cancel_before_model_run_persists_failed_run():
    repository = _repository()
    runnable = _runnable(TestModel(call_tools=[]))
    stream = runnable.stream_async(
        query="cancel me",
        agent_run_repository=repository,
        agent_run_session_id="session",
    )

    event, run = await stream.__anext__()
    assert event.value == "start"
    assert run.status.value == "executing"

    await stream.aclose()
    repository.update_agent_run_async.assert_called()
    saved_run = repository.update_agent_run_async.call_args.args[1]
    assert saved_run.status.value == "failed"
    assert "cancelled" in saved_run.error


@pytest.mark.asyncio
async def test_path_based_skill_is_unsupported():
    skill_retriever = AsyncMock()
    skill_retriever.get_skill_async = AsyncMock(
        return_value=SkillConfig(
            id="external",
            description="External skill",
            path="/tmp/external-skill",
        )
    )
    runnable = _runnable(TestModel(call_tools=[]))

    with pytest.raises(RuntimeError, match="path-based skills are not supported"):
        await _events(
            runnable,
            query="use skill",
            skill_retriever=skill_retriever,
            skill_ids=["external"],
        )
