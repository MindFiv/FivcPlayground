"""
Tests for LangChain tool implementations.

Tests the ToolImpl, ToolRetrieverImpl, and ToolRetrieverProviderImpl classes from
fivcplayground.implements.tools_langchain module.
"""

from unittest.mock import MagicMock

import pytest

from fivcglue.implements.utils import ComponentSite
from fivcplayground.implements.tools_langchain import (
    ToolImpl,
    ToolRetrieverImpl,
    ToolRetrieverProviderImpl,
)
from fivcplayground.interfaces import (
    ITool,
    IToolRetriever,
    IToolRetrieverProvider,
    ISetting,
    ISettingProvider,
    IEmbeddingDBProvider,
    IEmbeddingDB,
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


class TestToolImplLangChain:
    """Tests for LangChain ToolImpl class with lazy loading."""

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


class TestToolRetrieverImplLangChain:
    """Tests for LangChain ToolRetrieverImpl class."""

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
        tools = list(retriever.list_tools(names=["calculator"]))

        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_keyword_fallback(self, mock_setting):
        """Test search_tools falls back to keyword search when embeddings return nothing."""
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding.search_documents.return_value = []
        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.search_tools("calculator"))

        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_search_tools_semantic_search(self, mock_setting):
        """Test search_tools uses semantic search when embeddings are available."""
        from fivcplayground.interfaces import IEmbeddingDoc

        mock_embedding = MagicMock(spec=IEmbeddingDB)

        # Create mock embedding result
        mock_result = MagicMock(spec=IEmbeddingDoc)
        mock_result.metadata = {"tool_name": "calculator"}
        mock_embedding.search_documents.return_value = [mock_result]

        settings = [mock_setting]

        retriever = ToolRetrieverImpl(mock_embedding, settings)
        tools = list(retriever.search_tools("math"))

        assert len(tools) == 1
        assert tools[0].name == "calculator"
        mock_embedding.search_documents.assert_called_once_with(
            "math", num_documents=10
        )


class TestToolRetrieverProviderImplLangChain:
    """Tests for LangChain ToolRetrieverProviderImpl class."""

    def test_init(self, mock_component_site):
        """Test ToolRetrieverProviderImpl initialization."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolRetrieverProviderImpl(mock_component_site)

        assert provider._setting_provider is not None
        assert provider._embedding_provider is not None

    def test_implements_itoolretrieverprovider(self, mock_component_site):
        """Test that ToolRetrieverProviderImpl implements IToolRetrieverProvider interface."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolRetrieverProviderImpl(mock_component_site)
        assert isinstance(provider, IToolRetrieverProvider)

    def test_get_retriever_success(self, mock_component_site, mock_setting):
        """Test get_retriever returns a ToolRetrieverImpl when settings and embeddings are available."""
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

        provider = ToolRetrieverProviderImpl(mock_component_site)
        retriever = provider.get_retriever()

        assert retriever is not None
        assert isinstance(retriever, IToolRetriever)

    def test_get_retriever_no_settings(self, mock_component_site):
        """Test get_retriever returns None when no settings are available."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = []

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding = MagicMock(spec=IEmbeddingDB)
        mock_embedding_provider.get_embedding_db.return_value = mock_embedding

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolRetrieverProviderImpl(mock_component_site)
        retriever = provider.get_retriever()

        assert retriever is None

    def test_get_retriever_no_embeddings(self, mock_component_site, mock_setting):
        """Test get_retriever returns None when embeddings are not available."""
        mock_setting_provider = MagicMock(spec=ISettingProvider)
        mock_setting_provider.list_settings.return_value = [mock_setting]

        mock_embedding_provider = MagicMock(spec=IEmbeddingDBProvider)
        mock_embedding_provider.get_embedding_db.return_value = None

        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "tools"
        )
        mock_component_site.register_component(
            IEmbeddingDBProvider, mock_embedding_provider, "embeddings"
        )

        provider = ToolRetrieverProviderImpl(mock_component_site)
        retriever = provider.get_retriever()

        assert retriever is None

    def test_get_retriever_with_user_id(self, mock_component_site, mock_setting):
        """Test get_retriever passes user_id to providers."""
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

        provider = ToolRetrieverProviderImpl(mock_component_site)
        retriever = provider.get_retriever(user_id="user123")

        assert retriever is not None
        mock_setting_provider.list_settings.assert_called_once_with(user_id="user123")
        mock_embedding_provider.get_embedding_db.assert_called_once_with(
            "tools", user_id="user123"
        )
