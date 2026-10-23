import inspect

from fivcplayground.agents.types.base import AgentRunnable
from fivcplayground.agents.types.runnables import ParameterizedAgentRunnable
from fivcplayground.backends.adk.agents import AdkAgentRunnable
from fivcplayground.backends.strands.agents import StrandsAgentRunnable


def test_agent_runnable_contract_does_not_require_query():
    for method_name in ("run_async", "stream_async"):
        method = getattr(AgentRunnable, method_name)
        parameters = inspect.signature(method).parameters

        assert "query" not in parameters
        assert "kwargs" in parameters


def test_text_backends_can_define_their_own_query_parameter():
    for runnable_class in (
        StrandsAgentRunnable,
        AdkAgentRunnable,
        ParameterizedAgentRunnable,
    ):
        for method_name in ("run_async", "stream_async"):
            method = getattr(runnable_class, method_name)
            parameters = inspect.signature(method).parameters

            assert "query" in parameters
