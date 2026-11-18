"""
History replay must keep the most recent turns of a long session.

Repositories backed by a paged store (e.g. FivcCliche) return at most N runs.
Backends pass ``latest=True`` so a 35-turn session replays turns 6-35, oldest
first, instead of turns 1-30.
"""

from typing import List
from unittest.mock import MagicMock

import pytest

from fivcplayground.agents import (
    AgentRun,
    AgentRunContent,
    AgentRunRepository,
    AgentRunStatus,
)

TURNS = 35
PAGE_SIZE = 30
EXPECTED = list(range(TURNS - PAGE_SIZE + 1, TURNS + 1))  # turns 6..35


def _make_repository() -> AgentRunRepository:
    runs = [
        AgentRun(
            agent_id="agent",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text=f"Query {i}"),
            reply=AgentRunContent(text=f"Reply {i}"),
        )
        for i in range(1, TURNS + 1)
    ]

    async def list_agent_runs_async(
        session_id: str, latest: bool = False
    ) -> List[AgentRun]:
        return runs[-PAGE_SIZE:] if latest else runs[:PAGE_SIZE]

    repository = MagicMock(spec=AgentRunRepository)
    repository.list_agent_runs_async.side_effect = list_agent_runs_async
    return repository


def _expected_texts() -> List[str]:
    texts = []
    for i in EXPECTED:
        texts += [f"Query {i}", f"Reply {i}"]
    return texts


@pytest.mark.asyncio
async def test_strands_replays_latest_turns_in_order():
    pytest.importorskip("strands")
    from fivcplayground.backends.strands.agents import _list_messages

    messages = await _list_messages(_make_repository(), "session")

    assert [m["content"][0]["text"] for m in messages] == _expected_texts()
    assert [m["role"] for m in messages[:2]] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_adk_replays_latest_turns_in_order():
    pytest.importorskip("google.adk")
    from fivcplayground.backends.adk.agents import _list_events

    events = await _list_events(_make_repository(), "session")

    assert [e.content.parts[0].text for e in events] == _expected_texts()


@pytest.mark.asyncio
async def test_pipecat_replays_latest_turns_in_order():
    pytest.importorskip("pipecat")
    from fivcplayground.backends.pipecat.agents import _list_messages

    messages = await _list_messages(_make_repository(), "session")

    assert [m["content"] for m in messages] == _expected_texts()
    assert [m["role"] for m in messages[:2]] == ["user", "assistant"]
