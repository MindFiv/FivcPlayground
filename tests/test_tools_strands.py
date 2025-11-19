"""
Tests for tool implementations.

Tests the ToolImpl and ToolProviderImpl classes from
fivcplayground.implements.tools_strands module.
"""

from unittest.mock import MagicMock

import pytest

from fivcglue.implements.utils import ComponentSite
from fivcplayground.implements import ToolImpl, ToolProviderImpl
from fivcplayground.interfaces import (
    ITool,
    IToolProvider,
    ISetting,
    ISettingProvider,
    IEmbeddingDBProvider,
    IEmbeddingDB,
    EmbeddingResult,
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


class TestToolProviderImpl:
    """Tests for ToolProviderImpl class."""

    def test_init(self, mock_component_site, mock_setting):
        """Test ToolProviderImpl initialization."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)

        assert provider._embedding is mock_embedding
        assert provider._settings == {"calculator": mock_setting}
        assert provider._tools_cache == {}

    def test_implements_itoolprovider(self, mock_component_site, mock_setting):
        """Test that ToolProviderImpl implements IToolProvider interface."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        assert isinstance(provider, IToolProvider)

    def test_get_tool_existing(self, mock_component_site, mock_setting):
        """Test getting an existing tool."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tool = provider.get_tool("calculator")

        assert tool is not None
        assert tool.name == "calculator"
        assert tool.description == "Perform mathematical calculations"

    def test_get_tool_nonexistent(self, mock_component_site, mock_setting):
        """Test getting a non-existent tool returns None."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tool = provider.get_tool("nonexistent")

        assert tool is None

    def test_get_tool_caching(self, mock_component_site, mock_setting):
        """Test that ToolImpl instances are cached after first retrieval."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)

        # First call
        tool1 = provider.get_tool("calculator")
        # Second call
        tool2 = provider.get_tool("calculator")

        # Should be the same cached ToolImpl instance
        assert tool1 is tool2

    def test_get_tool_with_kwargs_override(self, mock_component_site, mock_setting):
        """Test that kwargs override setting values."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tool = provider.get_tool("calculator", description="Override description")

        # Verify description was overridden
        assert tool.description == "Override description"
        assert tool.name == "calculator"

    def test_get_tool_creation_error_value_error(
        self, mock_component_site, mock_setting
    ):
        """Test that ValueError in configuration is raised."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        # Simulate ValueError in setting.list()
        mock_setting.list.side_effect = ValueError("Invalid setting")
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)

        with pytest.raises(ValueError, match="Invalid setting"):
            provider.get_tool("calculator")

    def test_get_tool_creation_error_type_error(
        self, mock_component_site, mock_setting
    ):
        """Test that TypeError in configuration is raised."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        # Simulate TypeError in setting.list()
        mock_setting.list.side_effect = TypeError("Invalid type")
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)

        with pytest.raises(TypeError, match="Invalid type"):
            provider.get_tool("calculator")

    def test_get_tool_creation_error_attribute_error(
        self, mock_component_site, mock_setting
    ):
        """Test that AttributeError in configuration is raised."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        # Simulate AttributeError in setting.list()
        mock_setting.list.side_effect = AttributeError("Missing attribute")
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)

        with pytest.raises(AttributeError, match="Missing attribute"):
            provider.get_tool("calculator")

    def test_list_tools_all(self, mock_component_site):
        """Test listing all available tools."""
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

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.list_tools())

        assert len(tools) == 2
        assert tools[0].name == "calculator"
        assert tools[1].name == "weather"

    def test_list_tools_with_names(self, mock_component_site):
        """Test listing specific tools by name."""
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

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.list_tools(names=["calculator", "weather"]))

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "calculator" in tool_names
        assert "weather" in tool_names

    def test_list_tools_with_partial_failures(self, mock_component_site):
        """Test that list_tools returns successfully configured tools."""
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

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.list_tools())

        # Both tools should be returned
        assert len(tools) == 2
        assert tools[0].name == "calculator"
        assert tools[1].name == "weather"

    def test_search_tools_with_embeddings(self, mock_component_site):
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

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        # Setup embedding search results
        result1 = MagicMock(spec=EmbeddingResult)
        result1.metadata = {"tool_name": "calculator"}
        result1.score = 0.9

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = [result1]
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.search_tools(query="math"))

        # Verify search was performed
        mock_embedding.search_documents.assert_called_once_with(
            "math", num_documents=10
        )

        # Verify tools were returned
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_fallback_to_keyword_search(self, mock_component_site):
        """Test fallback to keyword search when embeddings are not available."""
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

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        # Create embedding that returns no results (simulating no embeddings)
        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = []
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.search_tools(query="math"))

        # Verify keyword search found the tool
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_keyword_search_case_insensitive(self, mock_component_site):
        """Test keyword search is case-insensitive."""
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "calculator"
        setting1.list.return_value = [
            ("name", "calculator"),
            ("description", "Perform mathematical calculations"),
        ]

        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [setting1]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = []
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolProviderImpl(mock_component_site)
        tools = list(provider.search_tools(query="MATH"))

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
