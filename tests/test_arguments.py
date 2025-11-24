"""
Tests for argument handling utilities.

Tests verify:
- DefaultKwargs initialization
- DefaultKwargs merging behavior
- DefaultKwargs callable interface
- Edge cases and error handling
"""

from fivcplayground.utils.types.arguments import DefaultKwargs


class TestDefaultKwargs:
    """Test DefaultKwargs class."""

    def test_initialization(self):
        """Test DefaultKwargs initialization."""
        defaults = DefaultKwargs({"key1": "value1", "key2": "value2"})

        assert defaults["key1"] == "value1"
        assert defaults["key2"] == "value2"
        assert len(defaults) == 2

    def test_dict_interface(self):
        """Test that DefaultKwargs behaves like a dict."""
        defaults = DefaultKwargs({"a": 1, "b": 2})

        assert "a" in defaults
        assert "c" not in defaults
        assert list(defaults.keys()) == ["a", "b"]
        assert list(defaults.values()) == [1, 2]

    def test_call_merges_with_none_values(self):
        """Test that calling merges defaults with None values."""
        defaults = DefaultKwargs({"key1": "default1", "key2": "default2"})
        other = {"key1": None, "key3": "value3"}

        result = defaults(other)

        assert result["key1"] == "default1"  # None replaced with default
        assert result["key2"] == "default2"  # Added from defaults
        assert result["key3"] == "value3"  # Kept from other

    def test_call_preserves_non_none_values(self):
        """Test that calling preserves non-None values from other dict."""
        defaults = DefaultKwargs({"key1": "default1", "key2": "default2"})
        other = {"key1": "override1", "key3": "value3"}

        result = defaults(other)

        assert result["key1"] == "override1"  # Non-None value preserved
        assert result["key2"] == "default2"  # Added from defaults
        assert result["key3"] == "value3"  # Kept from other

    def test_call_returns_default_kwargs(self):
        """Test that calling returns a DefaultKwargs instance."""
        defaults = DefaultKwargs({"key": "value"})
        result = defaults({})

        assert isinstance(result, DefaultKwargs)

    def test_call_with_empty_other(self):
        """Test calling with empty other dict."""
        defaults = DefaultKwargs({"key1": "value1", "key2": "value2"})
        result = defaults({})

        assert result["key1"] == "value1"
        assert result["key2"] == "value2"

    def test_call_with_empty_defaults(self):
        """Test calling with empty defaults."""
        defaults = DefaultKwargs({})
        other = {"key1": "value1", "key2": "value2"}

        result = defaults(other)

        assert result["key1"] == "value1"
        assert result["key2"] == "value2"

    def test_call_with_zero_values(self):
        """Test that zero values are not replaced."""
        defaults = DefaultKwargs({"count": 10})
        other = {"count": 0}

        result = defaults(other)

        assert result["count"] == 0  # Zero is not None, so it's preserved

    def test_call_with_false_values(self):
        """Test that False values are not replaced."""
        defaults = DefaultKwargs({"enabled": True})
        other = {"enabled": False}

        result = defaults(other)

        assert result["enabled"] is False  # False is not None, so it's preserved

    def test_call_with_empty_string_values(self):
        """Test that empty string values are not replaced."""
        defaults = DefaultKwargs({"name": "default_name"})
        other = {"name": ""}

        result = defaults(other)

        assert result["name"] == ""  # Empty string is not None, so it's preserved

    def test_chaining_calls(self):
        """Test chaining multiple calls."""
        defaults = DefaultKwargs({"a": 1, "b": 2, "c": 3})

        result1 = defaults({"a": None, "d": 4})
        result2 = result1({"b": None, "e": 5})

        assert result2["a"] == 1  # From first defaults
        assert result2["b"] == 2  # From first result
        assert result2["c"] == 3  # From first defaults
        assert result2["d"] == 4  # From first other
        assert result2["e"] == 5  # From second other

    def test_nested_dict_values(self):
        """Test with nested dict values."""
        defaults = DefaultKwargs({"config": {"nested": "value"}})
        other = {"config": None}

        result = defaults(other)

        assert result["config"] == {"nested": "value"}

    def test_list_values(self):
        """Test with list values."""
        defaults = DefaultKwargs({"items": [1, 2, 3]})
        other = {"items": None}

        result = defaults(other)

        assert result["items"] == [1, 2, 3]

    def test_mixed_types(self):
        """Test with mixed value types."""
        defaults = DefaultKwargs(
            {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "list": [1, 2],
                "dict": {"key": "value"},
            }
        )
        other = {
            "string": None,
            "number": None,
            "float": None,
            "bool": None,
            "list": None,
            "dict": None,
        }

        result = defaults(other)

        assert result["string"] == "text"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["list"] == [1, 2]
        assert result["dict"] == {"key": "value"}
