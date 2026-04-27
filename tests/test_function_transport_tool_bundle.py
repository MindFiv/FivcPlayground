#!/usr/bin/env python3
"""
Tests for FUNCTION transport support in create_tool_bundle.

Covers:
- DynamicFunc utility (unit tests)
- StrandsToolBackend.create_tool_bundle() with FUNCTION transport
"""

import pytest
from fivcplayground.backends.strands.tools import StrandsToolBackend, StrandsToolBundle
from fivcplayground.tools.types import FunctionToolBundle
from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.utils import DynamicFunc

BackendImpls = [StrandsToolBackend]


# ---------------------------------------------------------------------------
# Unit tests: DynamicFunc
# ---------------------------------------------------------------------------


class TestDynamicFunc:
    def test_known_function(self):
        func = DynamicFunc("fivcplayground.tools.calculator.calculator")
        assert callable(func)

    def test_clock_function(self):
        func = DynamicFunc("fivcplayground.tools.clock.clock")
        assert callable(func)

    def test_stdlib_function(self):
        import math

        func = DynamicFunc("math.sqrt")
        assert callable(func)
        assert func(4) == math.sqrt(4)

    def test_invalid_module_raises_import_error(self):
        with pytest.raises(ImportError):
            DynamicFunc("nonexistent_xyz.func")

    def test_missing_attribute_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            DynamicFunc("math.nonexistent_function_xyz")

    def test_path_without_dot_raises_value_error(self):
        with pytest.raises(ValueError, match="must contain at least one dot"):
            DynamicFunc("nodot")

    def test_non_callable_attribute_raises_value_error(self):
        # math.pi is a float, not callable
        with pytest.raises(ValueError, match="is not callable"):
            DynamicFunc("math.pi")

    def test_name_and_doc_proxied(self):
        func = DynamicFunc("fivcplayground.tools.calculator.calculator")
        import fivcplayground.tools.calculator as m

        assert func.__name__ == m.calculator.__name__
        assert func.__doc__ == m.calculator.__doc__

    def test_dotpath_stored(self):
        dotpath = "fivcplayground.tools.clock.clock"
        func = DynamicFunc(dotpath)
        assert func._dotpath == dotpath


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
        assert isinstance(bundle, FunctionToolBundle)

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
        assert not isinstance(bundle, FunctionToolBundle)

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
        assert isinstance(bundle, FunctionToolBundle)
        async with bundle.setup() as tools:
            assert len(tools) == 1
            assert tools[0].name == "clock"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
