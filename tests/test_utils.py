#!/usr/bin/env python3
"""
Tests for the utils module.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from fivcplayground.utils import (
    LazyValue,
    OutputDir,
)
from fivcplayground.utils.types.runnables import Runnable, ProxyRunnable


class TestLazyValue:
    """Test the LazyValue class."""

    def test_lazy_evaluation(self):
        """Test that value is computed lazily."""
        call_count = 0

        def getter():
            nonlocal call_count
            call_count += 1
            return "computed_value"

        lazy = LazyValue(getter)
        assert call_count == 0  # Not called yet

        value = lazy._ensure()
        assert call_count == 1  # Called once
        assert value == "computed_value"

        value2 = lazy._ensure()
        assert call_count == 1  # Still only called once (cached)
        assert value2 == "computed_value"

    def test_call_no_args(self):
        """Test calling LazyValue with no arguments."""
        lazy = LazyValue(lambda: "value")
        result = lazy()

        assert result == "value"

    def test_call_with_callable_value(self):
        """Test calling LazyValue when underlying value is callable."""

        def inner_func(x, y):
            return x + y

        lazy = LazyValue(lambda: inner_func)
        result = lazy(5, 10)

        assert result == 15

    def test_call_with_non_callable_value(self):
        """Test calling LazyValue with args when value is not callable."""
        lazy = LazyValue(lambda: "not_callable")

        with pytest.raises(TypeError, match="Underlying value is not callable"):
            lazy("arg")

    def test_getattr(self):
        """Test attribute access on LazyValue."""

        class TestObj:
            def __init__(self):
                self.attr = "test_value"

        lazy = LazyValue(lambda: TestObj())
        assert lazy.attr == "test_value"

    def test_setattr(self):
        """Test setting attributes on LazyValue."""

        class TestObj:
            def __init__(self):
                self.attr = "initial"

        lazy = LazyValue(lambda: TestObj())
        lazy.attr = "modified"

        assert lazy.attr == "modified"

    def test_getitem(self):
        """Test item access on LazyValue."""
        lazy = LazyValue(lambda: {"key": "value"})
        assert lazy["key"] == "value"

    def test_setitem(self):
        """Test setting items on LazyValue."""
        lazy = LazyValue(lambda: {"key": "value"})
        lazy["key"] = "new_value"

        assert lazy["key"] == "new_value"

    def test_delitem(self):
        """Test deleting items from LazyValue."""
        lazy = LazyValue(lambda: {"key1": "value1", "key2": "value2"})
        del lazy["key1"]

        assert "key1" not in lazy
        assert "key2" in lazy

    def test_iter(self):
        """Test iteration over LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3])
        result = list(lazy)

        assert result == [1, 2, 3]

    def test_len(self):
        """Test len() on LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3, 4])
        assert len(lazy) == 4

    def test_contains(self):
        """Test 'in' operator on LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3])
        assert 2 in lazy
        assert 5 not in lazy

    def test_bool(self):
        """Test bool conversion of LazyValue."""
        lazy_true = LazyValue(lambda: [1, 2, 3])
        lazy_false = LazyValue(lambda: [])

        assert bool(lazy_true) is True
        assert bool(lazy_false) is False

    def test_repr_uninitialized(self):
        """Test repr of uninitialized LazyValue."""
        lazy = LazyValue(lambda: "value")
        assert repr(lazy) == "LazyValue(<uninitialized>)"

    def test_repr_initialized(self):
        """Test repr of initialized LazyValue."""
        lazy = LazyValue(lambda: "value")
        lazy._ensure()
        assert repr(lazy) == "LazyValue('value')"

    def test_str(self):
        """Test str conversion of LazyValue."""
        lazy = LazyValue(lambda: "test_string")
        assert str(lazy) == "test_string"

    def test_equality(self):
        """Test equality comparison of LazyValue."""
        lazy1 = LazyValue(lambda: "value")
        lazy2 = LazyValue(lambda: "value")
        lazy3 = LazyValue(lambda: "other")

        assert lazy1 == lazy2
        assert lazy1 == "value"
        assert lazy1 != lazy3
        assert lazy1 != "other"


class TestOutputDir:
    """Test the OutputDir class."""

    def test_init_default(self):
        """Test OutputDir initialization with default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["WORKSPACE"] = tmpdir
            output_dir = OutputDir()

            # Use resolve() to handle symlinks on macOS
            assert output_dir.base.resolve() == Path(tmpdir).resolve()
            assert output_dir.base.exists()

    def test_init_custom_path(self):
        """Test OutputDir initialization with custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "custom")
            output_dir = OutputDir(custom_path)

            assert str(output_dir) == str(Path(custom_path).resolve())
            assert output_dir.base.exists()

    def test_str_conversion(self):
        """Test string conversion of OutputDir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            assert str(output_dir) == str(Path(tmpdir).resolve())

    def test_context_manager(self):
        """Test OutputDir as context manager."""
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)

            with output_dir:
                assert os.getcwd() == str(output_dir)

            assert os.getcwd() == original_cwd

    def test_subdir(self):
        """Test creating subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            subdir = output_dir.subdir("test_subdir")

            assert isinstance(subdir, OutputDir)
            assert "test_subdir" in str(subdir)
            assert subdir.base.exists()

    def test_cleanup(self):
        """Test cleanup method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "to_cleanup")
            output_dir = OutputDir(test_dir)

            assert output_dir.base.exists()
            output_dir.cleanup()
            assert not output_dir.base.exists()


class TestLazyValueAdditionalOperations:
    """Test additional LazyValue operations for better coverage."""

    def test_delattr(self):
        """Test deleting attributes from LazyValue."""

        class TestObj:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = "value2"

        lazy = LazyValue(lambda: TestObj())
        del lazy.attr1

        assert not hasattr(lazy, "attr1")
        assert hasattr(lazy, "attr2")

    def test_container_operations(self):
        """Test container operations on LazyValue."""
        lazy = LazyValue(lambda: {"key": "value", "num": 42})

        assert lazy["key"] == "value"
        assert lazy["num"] == 42

        lazy["new_key"] = "new_value"
        assert lazy["new_key"] == "new_value"

        del lazy["new_key"]
        assert "new_key" not in lazy

    def test_iteration(self):
        """Test iteration over LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3, 4, 5])

        result = list(lazy)
        assert result == [1, 2, 3, 4, 5]

    def test_length(self):
        """Test len() on LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3])
        assert len(lazy) == 3

    def test_contains(self):
        """Test 'in' operator on LazyValue."""
        lazy = LazyValue(lambda: [1, 2, 3])
        assert 2 in lazy
        assert 5 not in lazy

    def test_bool_conversion(self):
        """Test bool conversion of LazyValue."""
        lazy_true = LazyValue(lambda: [1, 2, 3])
        lazy_false = LazyValue(lambda: [])

        assert bool(lazy_true) is True
        assert bool(lazy_false) is False

    def test_context_manager(self):
        """Test LazyValue as context manager."""

        class MockContextManager:
            def __init__(self):
                self.entered = False
                self.exited = False

            def __enter__(self):
                self.entered = True
                return self

            def __exit__(self, exc_type, exc, tb):
                self.exited = True
                return False

        mock_cm = MockContextManager()
        lazy = LazyValue(lambda: mock_cm)

        with lazy as cm:
            assert cm.entered is True

        assert mock_cm.exited is True

    def test_equality(self):
        """Test equality comparison of LazyValue."""
        lazy1 = LazyValue(lambda: "value")
        lazy2 = LazyValue(lambda: "value")
        lazy3 = LazyValue(lambda: "different")

        assert lazy1 == lazy2
        assert lazy1 == "value"
        assert lazy1 != lazy3
        assert lazy1 != "different"

    def test_repr(self):
        """Test repr of LazyValue."""
        lazy = LazyValue(lambda: "test_value")

        # Before evaluation
        repr_before = repr(lazy)
        assert "uninitialized" in repr_before

        # After evaluation
        _ = lazy._ensure()
        repr_after = repr(lazy)
        assert "test_value" in repr_after

    def test_str(self):
        """Test str of LazyValue."""
        lazy = LazyValue(lambda: "test_string")
        assert str(lazy) == "test_string"


class TestRunnable:
    """Test the Runnable abstract base class."""

    def test_runnable_call_delegates_to_run(self):
        """Test that __call__ delegates to run method."""

        class TestRunnable(Runnable):
            @property
            def id(self):
                return "test-runnable"

            @property
            def name(self):
                return "TestRunnable"

            def run(self, **kwargs):
                return {"result": "sync"}

            async def run_async(self, **kwargs):
                return {"result": "async"}

        runnable = TestRunnable()
        result = runnable(test_param="value")

        assert result == {"result": "sync"}

    def test_runnable_properties(self):
        """Test Runnable id and name properties."""

        class TestRunnable(Runnable):
            @property
            def id(self):
                return "my-id"

            @property
            def name(self):
                return "MyName"

            def run(self, **kwargs):
                return {}

            async def run_async(self, **kwargs):
                return {}

        runnable = TestRunnable()
        assert runnable.id == "my-id"
        assert runnable.name == "MyName"


class TestProxyRunnable:
    """Test the ProxyRunnable class."""

    def test_proxy_runnable_delegates_to_wrapped(self):
        """Test that ProxyRunnable delegates to wrapped runnable."""
        mock_runnable = Mock(spec=Runnable)
        mock_runnable.id = "wrapped-id"
        mock_runnable.name = "WrappedRunnable"
        mock_runnable.run.return_value = {"result": "wrapped"}

        proxy = ProxyRunnable(mock_runnable)

        assert proxy.id == "wrapped-id"
        assert proxy.name == "WrappedRunnable"
        result = proxy.run()
        assert result == {"result": "wrapped"}

    def test_proxy_runnable_merges_kwargs(self):
        """Test that ProxyRunnable merges kwargs correctly."""
        mock_runnable = Mock(spec=Runnable)
        mock_runnable.id = "test"
        mock_runnable.name = "Test"
        mock_runnable.run.return_value = {}

        proxy = ProxyRunnable(mock_runnable, default_param="default_value")
        proxy.run(other_param="other_value")

        # Check that both kwargs were passed
        call_kwargs = mock_runnable.run.call_args[1]
        assert call_kwargs["default_param"] == "default_value"
        assert call_kwargs["other_param"] == "other_value"

    def test_proxy_runnable_kwargs_override(self):
        """Test that passed kwargs are preserved (setdefault doesn't override)."""
        mock_runnable = Mock(spec=Runnable)
        mock_runnable.id = "test"
        mock_runnable.name = "Test"
        mock_runnable.run.return_value = {}

        proxy = ProxyRunnable(mock_runnable, param="proxy_value")
        proxy.run(param="override_value")

        # Check that override value was preserved (setdefault doesn't override existing keys)
        call_kwargs = mock_runnable.run.call_args[1]
        assert call_kwargs["param"] == "override_value"  # setdefault keeps original

    @pytest.mark.asyncio
    async def test_proxy_runnable_async_delegates(self):
        """Test that ProxyRunnable delegates async calls."""
        mock_runnable = AsyncMock(spec=Runnable)
        mock_runnable.id = "test"
        mock_runnable.name = "Test"
        mock_runnable.run_async.return_value = {"result": "async"}

        proxy = ProxyRunnable(mock_runnable)
        result = await proxy.run_async()

        assert result == {"result": "async"}
        mock_runnable.run_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_proxy_runnable_async_merges_kwargs(self):
        """Test that ProxyRunnable merges kwargs in async calls."""
        from unittest.mock import AsyncMock

        mock_runnable = AsyncMock(spec=Runnable)
        mock_runnable.id = "test"
        mock_runnable.name = "Test"
        mock_runnable.run_async.return_value = {}

        proxy = ProxyRunnable(mock_runnable, async_param="async_value")
        await proxy.run_async(other_param="other_value")

        # Check that both kwargs were passed
        call_kwargs = mock_runnable.run_async.call_args[1]
        assert call_kwargs["async_param"] == "async_value"
        assert call_kwargs["other_param"] == "other_value"


if __name__ == "__main__":
    pytest.main([__file__])
