"""
Tests for tool implementations.

Tests the ToolImpl and ToolRetrieverImpl classes from
fivcplayground.implements.tools_strands module.
"""

from unittest.mock import MagicMock

import pytest

from fivcglue.implements.utils import ComponentSite
from fivcplayground.implements import ToolImpl, ToolRetrieverImpl
from fivcplayground.interfaces import (
    ITool,
    IToolRetriever,
    ISetting,
    ISettingProvider,
    IEmbeddingDBProvider,
    IEmbeddingDB,
    IEmbeddingResult,
)


@pytest.fixture
def mock_component_site():
    """Create a mock component site for testing."""
    return ComponentSite()


@pytest.fixture
def mock_setting_provider():
    """Create a mock setting provider for testing."""
    provider = MagicMock(spec=ISettingProvider)
    return provider


@pytest.fixture
def mock_setting():
    """Create a mock setting for testing."""
    setting = MagicMock(spec=ISetting)
    setting.name = "calculator"
    setting.list.return_value = [
        ("name", "calculator"),
        ("description", "Perform mathematical calculations"),
    ]
    return setting


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider for testing."""
    provider = MagicMock(spec=IEmbeddingDBProvider)
    return provider


@pytest.fixture
def mock_embedding():
    """Create a mock embedding for testing."""
    embedding = MagicMock(spec=IEmbeddingDB)
    embedding.name = "tools_search"
    embedding.add_document.return_value = []
    embedding.search_documents.return_value = []
    return embedding


class TestToolImpl:
    """Tests for ToolImpl class with lazy loading."""

    def test_init(self):
        """Test ToolImpl initialization."""
        tool = ToolImpl("calculator", description="Math tool")

        assert tool.name == "calculator"
        assert tool.description == "Math tool"
        assert tool._underlying is None

    def test_name_property(self):
        """Test name property."""
        tool = ToolImpl("weather", description="Weather tool")

        assert tool.name == "weather"

    def test_description_property(self):
        """Test description property."""
        tool = ToolImpl("search", description="Search the web")

        assert tool.description == "Search the web"

    def test_get_underlying_with_none(self):
        """Test get_underlying returns None when not set."""
        tool = ToolImpl("calculator", description="Math tool")

        result = tool.get_underlying()
        assert result is None

    def test_get_underlying_with_tool(self):
        """Test get_underlying returns the underlying tool."""
        mock_underlying = MagicMock()
        tool = ToolImpl(
            "calculator", description="Math tool", underlying=mock_underlying
        )

        result = tool.get_underlying()
        assert result is mock_underlying

    def test_implements_itool(self):
        """Test that ToolImpl implements ITool interface."""
        tool = ToolImpl("test", description="Test tool")
        assert isinstance(tool, ITool)


class TestToolRetrieverImpl:
    """Tests for ToolRetrieverImpl class."""

    def test_init(self, mock_setting):
        """Test ToolRetrieverImpl initialization."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)

        assert retriever._embedding is mock_embedding
        assert retriever._settings == {"calculator": mock_setting}
        assert retriever._tools_cache == {}

    def test_implements_itoolretriever(self, mock_setting):
        """Test that ToolRetrieverImpl implements IToolRetriever interface."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        assert isinstance(retriever, IToolRetriever)

    def test_get_tool_existing(self, mock_setting):
        """Test getting an existing tool."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tool = retriever.get_tool("calculator")

        assert tool is not None
        assert tool.name == "calculator"
        assert tool.description == "Perform mathematical calculations"

    def test_get_tool_nonexistent(self, mock_setting):
        """Test getting a non-existent tool returns None."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tool = retriever.get_tool("nonexistent")

        assert tool is None

    def test_get_tool_caching(self, mock_setting):
        """Test that ToolImpl instances are cached after first retrieval."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)

        # First call
        tool1 = retriever.get_tool("calculator")
        # Second call
        tool2 = retriever.get_tool("calculator")

        # Should be the same cached ToolImpl instance
        assert tool1 is tool2

    def test_get_tool_with_kwargs_override(self, mock_setting):
        """Test that kwargs override setting values."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tool = retriever.get_tool("calculator", description="Override description")

        # Verify description was overridden
        assert tool.description == "Override description"
        assert tool.name == "calculator"

    def test_get_tool_creation_error_value_error(self, mock_setting):
        """Test that ValueError in configuration is raised."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        # Simulate ValueError in setting.list()
        mock_setting.list.side_effect = ValueError("Invalid setting")
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)

        with pytest.raises(ValueError, match="Invalid setting"):
            retriever.get_tool("calculator")

    def test_get_tool_creation_error_type_error(self, mock_setting):
        """Test that TypeError in configuration is raised."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        # Simulate TypeError in setting.list()
        mock_setting.list.side_effect = TypeError("Invalid type")
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)

        with pytest.raises(TypeError, match="Invalid type"):
            retriever.get_tool("calculator")

    def test_get_tool_creation_error_attribute_error(self, mock_setting):
        """Test that AttributeError in configuration is raised."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        # Simulate AttributeError in setting.list()
        mock_setting.list.side_effect = AttributeError("Missing attribute")
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)

        with pytest.raises(AttributeError, match="Missing attribute"):
            retriever.get_tool("calculator")

    def test_list_tools_all(self):
        """Test listing all available tools."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)

        # Create multiple mock settings
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Math tool"),
        ]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "weather"
        setting2.list.return_value = [
            ("name", "weather"),
            ("description", "Weather tool"),
        ]

        settings = [setting1, setting2]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.list_tools())

        assert len(tools) == 2
        assert tools[0].name == "calculator"
        assert tools[1].name == "weather"

    def test_list_tools_with_names(self):
        """Test listing specific tools by name."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)

        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Math tool"),
        ]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "weather"
        setting2.list.return_value = [
            ("name", "weather"),
            ("description", "Weather tool"),
        ]

        settings = [setting1, setting2]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.list_tools(names=["calculator", "weather"]))

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "calculator" in tool_names
        assert "weather" in tool_names

    def test_list_tools_with_partial_failures(self):
        """Test that list_tools returns successfully configured tools."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)

        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Math tool"),
        ]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "weather"
        setting2.list.return_value = [
            ("name", "weather"),
            ("description", "Weather tool"),
        ]

        settings = [setting1, setting2]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.list_tools())

        # Both tools should be returned
        assert len(tools) == 2
        assert tools[0].name == "calculator"
        assert tools[1].name == "weather"

    def test_search_tools_with_embeddings(self, mock_embedding):
        """Test semantic search using embeddings."""
        # Setup settings
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Perform mathematical calculations"),
        ]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "weather"
        setting2.list.return_value = [
            ("name", "weather"),
            ("description", "Get weather information"),
        ]

        settings = [setting1, setting2]

        # Setup embedding search results
        result1 = MagicMock(spec=IEmbeddingResult)
        result1.metadata = {"tool_name": "calculator"}
        result1.score = 0.9

        mock_embedding.search_documents.return_value = [result1]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.search_tools("math"))

        # Verify search was performed
        mock_embedding.search_documents.assert_called_once_with(
            "math", num_documents=10
        )

        # Verify tools were returned
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_fallback_to_keyword_search(self):
        """Test fallback to keyword search when embeddings are not available."""
        # Create embedding that returns no results (simulating no embeddings)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = []

        # Setup settings
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Perform mathematical calculations"),
        ]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "weather"
        setting2.list.return_value = [
            ("name", "weather"),
            ("description", "Get weather information"),
        ]

        settings = [setting1, setting2]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.search_tools("math"))

        # Verify keyword search found the tool
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_keyword_search_case_insensitive(self):
        """Test keyword search is case-insensitive."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = []

        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Perform mathematical calculations"),
        ]

        settings = [setting1]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.search_tools("MATH"))

        # Verify case-insensitive search found the tool
        assert len(tools) == 1
        assert tools[0].name == "calculator"


class TestCalculatorToolImpl:
    """Tests for CalculatorToolImpl class."""

    def test_calculator_tool_init(self):
        """Test CalculatorToolImpl initialization."""
        from fivcplayground.implements.tools_strands import CalculatorToolImpl

        tool = CalculatorToolImpl()
        assert tool.name == "calculator"
        assert "mathematical calculations" in tool.description.lower()
        assert tool.get_underlying() is not None

    def test_calculator_tool_implements_itool(self):
        """Test that CalculatorToolImpl implements ITool interface."""
        from fivcplayground.implements.tools_strands import CalculatorToolImpl

        tool = CalculatorToolImpl()
        assert isinstance(tool, ITool)

    def test_calculator_tool_properties(self):
        """Test CalculatorToolImpl properties."""
        from fivcplayground.implements.tools_strands import CalculatorToolImpl

        tool = CalculatorToolImpl()
        assert tool.name == "calculator"
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0


class TestClockToolImpl:
    """Tests for ClockToolImpl class."""

    def test_clock_tool_init(self):
        """Test ClockToolImpl initialization."""
        from fivcplayground.implements.tools_strands import ClockToolImpl

        tool = ClockToolImpl()
        assert tool.name == "clock"
        assert "time" in tool.description.lower()
        assert tool.get_underlying() is not None

    def test_clock_tool_implements_itool(self):
        """Test that ClockToolImpl implements ITool interface."""
        from fivcplayground.implements.tools_strands import ClockToolImpl

        tool = ClockToolImpl()
        assert isinstance(tool, ITool)

    def test_clock_tool_properties(self):
        """Test ClockToolImpl properties."""
        from fivcplayground.implements.tools_strands import ClockToolImpl

        tool = ClockToolImpl()
        assert tool.name == "clock"
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
