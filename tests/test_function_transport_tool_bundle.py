#!/usr/bin/env python3
"""
Tests for FUNCTION transport support in create_tool_bundle.

Covers:
- DynamicCallable utility (unit tests)
- StrandsToolBackend.create_tool_bundle() with FUNCTION transport
"""

import pytest
from fivcplayground.agents.types.spans import AgentRunToolSpan
from fivcplayground.backends.strands.tools import StrandsToolBackend, StrandsToolBundle
from fivcplayground.tools.types import CallableToolBundle
from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.utils import DynamicCallable

BackendImpls = [StrandsToolBackend]


async def async_configured_tool(value: str = "ok") -> str:
    """Return an async value."""
    return f"async:{value}"


class ContextClassTool:
    """Return user id from runtime context."""

    def __init__(self, **context):
        self.context = context

    def __call__(self) -> str:
        """Do not use this __call__ docstring."""
        return self.context["user_id"]


class MultiContextClassTool:
    """Return multiple values from runtime context."""

    def __init__(self, **context):
        self.context = context

    def __call__(self) -> str:
        """Do not use this __call__ docstring."""
        return f"{self.context['user_id']}:{self.context['request_id']}"


class AsyncContextClassTool:
    """Return user id asynchronously from runtime context."""

    def __init__(self, **context):
        self.context = context

    async def __call__(self) -> str:
        """Do not use this __call__ docstring."""
        return f"async:{self.context['user_id']}"


class NoDocstringClassTool:
    """Return a fixed value without a __call__ docstring."""

    def __call__(self) -> str:
        return "no-docstring"


class NonCallableClassTool:
    def __init__(self, **context):
        self.context = context


# ---------------------------------------------------------------------------
# Unit tests: DynamicCallable
# ---------------------------------------------------------------------------


class TestDynamicCallable:
    def test_known_function(self):
        func = DynamicCallable("fivcplayground.tools.calculator.calculator")
        assert callable(func)
        assert func.kind == "function"

    def test_clock_function(self):
        func = DynamicCallable("fivcplayground.tools.clock.clock")
        assert callable(func)
        assert func.kind == "function"

    def test_known_class(self):
        func = DynamicCallable(f"{__name__}.ContextClassTool")
        assert callable(func)
        assert func.kind == "class"
        assert func(user_id="u-123")() == "u-123"

    def test_stdlib_function(self):
        import math

        func = DynamicCallable("math.sqrt")
        assert callable(func)
        assert func(4) == math.sqrt(4)

    def test_invalid_module_raises_import_error(self):
        with pytest.raises(ImportError):
            DynamicCallable("nonexistent_xyz.func")

    def test_missing_attribute_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            DynamicCallable("math.nonexistent_function_xyz")

    def test_path_without_dot_raises_value_error(self):
        with pytest.raises(ValueError, match="must contain at least one dot"):
            DynamicCallable("nodot")

    def test_non_callable_attribute_raises_value_error(self):
        # math.pi is a float, not callable
        with pytest.raises(ValueError, match="is not callable"):
            DynamicCallable("math.pi")

    def test_name_and_doc_proxied(self):
        func = DynamicCallable("fivcplayground.tools.calculator.calculator")
        import fivcplayground.tools.calculator as m

        assert func.__name__ == m.calculator.__name__
        assert func.__doc__ == m.calculator.__doc__

    def test_dotpath_stored(self):
        dotpath = "fivcplayground.tools.clock.clock"
        func = DynamicCallable(dotpath)
        assert func._dotpath == dotpath

    def test_class_name_is_snake_case(self):
        func = DynamicCallable(f"{__name__}.ContextClassTool")
        assert func.__name__ == "context_class_tool"


# ---------------------------------------------------------------------------
# Integration tests: create_tool_bundle with FUNCTION transport
# ---------------------------------------------------------------------------


class TestCreateToolBundleFunctionTransport:
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_returns_function_tool_bundle(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="my_bundle",
            description="A test bundle",
            transport="function",
            functions=["fivcplayground.tools.clock.clock"],
        )
        bundle = backend.create_tool_bundle(config)
        assert isinstance(bundle, CallableToolBundle)

    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_bundle_name_and_description(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="named_bundle",
            description="Bundle description here",
            transport="function",
            functions=["fivcplayground.tools.calculator.calculator"],
        )
        bundle = backend.create_tool_bundle(config)
        assert bundle.name == "named_bundle"
        assert bundle.description == "Bundle description here"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_bundle_setup_returns_tools(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="two_func_bundle",
            description="Clock and calculator",
            transport="function",
            functions=[
                "fivcplayground.tools.clock.clock",
                "fivcplayground.tools.calculator.calculator",
            ],
        )
        bundle = backend.create_tool_bundle(config)
        async with bundle.setup() as tools:
            assert len(tools) == 2
            names = {t.name for t in tools}
            assert "clock" in names
            assert "calculator" in names

    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_returns_callable_tool_bundle_for_class(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="class_bundle",
            description="A stateful class bundle",
            transport="function",
            functions=[f"{__name__}.ContextClassTool"],
        )
        bundle = backend.create_tool_bundle(config)
        assert isinstance(bundle, CallableToolBundle)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_class_bundle_setup_instantiates_with_context(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="class_bundle",
            description="A stateful class bundle",
            transport="function",
            functions=[f"{__name__}.ContextClassTool"],
        )
        bundle = backend.create_tool_bundle(config)
        async with bundle.setup(user_id="u-123") as tools:
            assert len(tools) == 1
            assert tools[0].name == "context_class_tool"
            assert tools[0].description == "Return user id from runtime context."
            assert tools[0].get_underlying()() == "u-123"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_class_bundle_setup_passes_each_context_key_as_keyword(
        self, BackendImpl
    ):
        backend = BackendImpl()
        config = ToolConfig(
            id="class_bundle",
            description="A stateful class bundle",
            transport="function",
            functions=[f"{__name__}.MultiContextClassTool"],
        )
        bundle = backend.create_tool_bundle(config)
        async with bundle.setup(user_id="u-123", request_id="r-456") as tools:
            assert len(tools) == 1
            assert tools[0].name == "multi_context_class_tool"
            assert (
                tools[0].description == "Return multiple values from runtime context."
            )
            assert tools[0].get_underlying()() == "u-123:r-456"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_class_bundle_requires_callable_instance(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="class_bundle",
            description="A stateful class bundle",
            transport="function",
            functions=[
                f"{__name__}.NonCallableClassTool",
            ],
        )
        bundle = backend.create_tool_bundle(config)
        with pytest.raises(ValueError, match="must implement __call__"):
            async with bundle.setup(user_id="u-123"):
                pass

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_mixed_function_and_class_bundle_setup_returns_all_tools(
        self, BackendImpl
    ):
        backend = BackendImpl()
        config = ToolConfig(
            id="mixed_bundle",
            description="Clock and stateful class tool",
            transport="function",
            functions=[
                "fivcplayground.tools.clock.clock",
                f"{__name__}.ContextClassTool",
            ],
        )
        bundle = backend.create_tool_bundle(config)
        assert isinstance(bundle, CallableToolBundle)
        async with bundle.setup(user_id="u-123") as tools:
            names = {tool.name for tool in tools}
            assert names == {"clock", "context_class_tool"}
            class_tool = next(
                tool for tool in tools if tool.name == "context_class_tool"
            )
            assert class_tool.get_underlying()() == "u-123"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_async_function_from_tool_config_remains_awaitable(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="async_bundle",
            description="An async function bundle",
            transport="function",
            functions=[f"{__name__}.async_configured_tool"],
        )
        bundle = backend.create_tool_bundle(config)
        async with bundle.setup() as tools:
            assert len(tools) == 1
            assert tools[0].name == "async_configured_tool"
            result = tools[0].get_underlying()(value="ok")
            assert await result == "async:ok"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_async_class_tool_from_tool_config_remains_awaitable(
        self, BackendImpl
    ):
        backend = BackendImpl()
        config = ToolConfig(
            id="async_class_bundle",
            description="An async class tool bundle",
            transport="function",
            functions=[f"{__name__}.AsyncContextClassTool"],
        )
        bundle = backend.create_tool_bundle(config)
        async with bundle.setup(user_id="u-123") as tools:
            assert len(tools) == 1
            assert tools[0].name == "async_context_class_tool"
            assert (
                tools[0].description
                == "Return user id asynchronously from runtime context."
            )
            result = tools[0].get_underlying()()
            assert await result == "async:u-123"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_tool_span_expands_configured_class_tool_with_snake_case_name(
        self, BackendImpl
    ):
        backend = BackendImpl()
        config = ToolConfig(
            id="class_bundle",
            description="A stateful class bundle",
            transport="function",
            functions=[f"{__name__}.ContextClassTool"],
        )

        class ConfigBackedRetriever:
            async def get_tool_async(self, name: str):
                if name == "class_bundle":
                    return backend.create_tool_bundle(config)
                return None

            def to_tool(self, dummy: bool = False):
                raise AssertionError("dummy tool should not be needed")

        async with AgentRunToolSpan(
            tool_retriever=ConfigBackedRetriever(),
            tool_ids=["class_bundle"],
            context={"user_id": "u-123"},
        ) as span:
            tools = span.tools

        assert [tool.name for tool in tools] == ["context_class_tool"]
        assert "ContextClassTool" not in {tool.name for tool in tools}
        assert tools[0].get_underlying()() == "u-123"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_class_tool_without_call_docstring_keeps_configured_name(
        self, BackendImpl
    ):
        backend = BackendImpl()
        config = ToolConfig(
            id="no_docstring_class_bundle",
            description="A class tool without a __call__ docstring",
            transport="function",
            functions=[f"{__name__}.NoDocstringClassTool"],
        )
        bundle = backend.create_tool_bundle(config)

        tool_context = bundle.setup()
        async with tool_context as tools:
            tool_names = [tool.name for tool in tools]

        assert tool_names == ["no_docstring_class_tool"]
        assert "__call__" not in tool_names
        assert (
            tools[0].description == "Return a fixed value without a __call__ docstring."
        )

    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_functions_none_raises_value_error(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="bad_bundle",
            description="No functions",
            transport="function",
            functions=None,
        )
        with pytest.raises(ValueError, match="'functions' is None or empty"):
            backend.create_tool_bundle(config)

    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_functions_empty_list_raises_value_error(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="bad_bundle",
            description="Empty functions list",
            transport="function",
            functions=[],
        )
        with pytest.raises(ValueError, match="'functions' is None or empty"):
            backend.create_tool_bundle(config)

    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    def test_invalid_dotted_path_raises_import_error(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="bad_bundle",
            description="Bad path",
            transport="function",
            functions=["nonexistent_xyz.func"],
        )
        with pytest.raises(ImportError):
            backend.create_tool_bundle(config)

    def test_non_function_transport_strands_still_works(self):
        backend = StrandsToolBackend()
        config = ToolConfig(
            id="stdio_bundle",
            description="MCP bundle",
            transport="stdio",
            command="python",
            args=["-m", "mcp_server"],
        )
        bundle = backend.create_tool_bundle(config)
        assert isinstance(bundle, StrandsToolBundle)
        assert not isinstance(bundle, CallableToolBundle)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("BackendImpl", BackendImpls)
    async def test_single_function_bundle(self, BackendImpl):
        backend = BackendImpl()
        config = ToolConfig(
            id="single_bundle",
            description="Just clock",
            transport="function",
            functions=["fivcplayground.tools.clock.clock"],
        )
        bundle = backend.create_tool_bundle(config)
        assert isinstance(bundle, CallableToolBundle)
        async with bundle.setup() as tools:
            assert len(tools) == 1
            assert tools[0].name == "clock"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
