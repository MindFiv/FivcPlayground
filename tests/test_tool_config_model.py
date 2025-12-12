#!/usr/bin/env python3
"""
Tests for ToolConfig Pydantic model validation.
"""

import json
import pytest
from pydantic import ValidationError

from fivcplayground.tools.types.base import ToolConfig, ToolConfigTransport


class TestToolConfigModel:
    """Tests for ToolConfig Pydantic model"""

    def test_create_with_stdio_transport(self):
        """Test creating ToolConfig with stdio transport"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="stdio",
            command="python",
            args=["script.py"],
        )
        assert config.id == "test_tool"
        assert config.description == "Test tool"
        assert config.transport == "stdio"
        assert config.command == "python"
        assert config.args == ["script.py"]

    def test_create_with_sse_transport(self):
        """Test creating ToolConfig with SSE transport"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="sse",
            url="http://localhost:8000/sse",
        )
        assert config.transport == "sse"
        assert config.url == "http://localhost:8000/sse"
        assert config.command is None

    def test_create_with_streamable_http_transport(self):
        """Test creating ToolConfig with streamable_http transport"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="streamable_http",
            url="http://localhost:8000",
        )
        assert config.transport == "streamable_http"
        assert config.url == "http://localhost:8000"

    def test_missing_required_id(self):
        """Test that missing id raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                description="Test tool",
                transport="stdio",
                command="python",
            )
        assert "id" in str(exc_info.value)

    def test_missing_required_description(self):
        """Test that missing description raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                id="test_tool",
                transport="stdio",
                command="python",
            )
        assert "description" in str(exc_info.value)

    def test_missing_required_transport(self):
        """Test that missing transport raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                id="test_tool",
                description="Test tool",
                command="python",
            )
        assert "transport" in str(exc_info.value)

    def test_invalid_transport_value(self):
        """Test that invalid transport value raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                id="test_tool",
                description="Test tool",
                transport="invalid_transport",
                command="python",
            )
        assert "transport" in str(exc_info.value)

    def test_optional_fields(self):
        """Test that optional fields can be omitted"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="stdio",
        )
        assert config.command is None
        assert config.args is None
        assert config.env is None
        assert config.url is None

    def test_with_environment_variables(self):
        """Test creating ToolConfig with environment variables"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="stdio",
            command="python",
            env={"API_KEY": "secret", "DEBUG": "true"},
        )
        assert config.env == {"API_KEY": "secret", "DEBUG": "true"}

    def test_model_dump(self):
        """Test model_dump serialization"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="stdio",
            command="python",
            args=["script.py"],
        )
        dumped = config.model_dump()
        assert dumped["id"] == "test_tool"
        assert dumped["description"] == "Test tool"
        assert dumped["transport"] == "stdio"
        assert dumped["command"] == "python"
        assert dumped["args"] == ["script.py"]

    def test_model_validate(self):
        """Test model_validate deserialization"""
        data = {
            "id": "test_tool",
            "description": "Test tool",
            "transport": "stdio",
            "command": "python",
            "args": ["script.py"],
        }
        config = ToolConfig.model_validate(data)
        assert config.id == "test_tool"
        assert config.description == "Test tool"

    def test_model_validate_json(self):
        """Test model_validate_json deserialization"""
        json_str = '{"id": "test_tool", "description": "Test tool", "transport": "stdio", "command": "python"}'
        config = ToolConfig.model_validate_json(json_str)
        assert config.id == "test_tool"
        assert config.description == "Test tool"

    def test_empty_description_is_valid(self):
        """Test that empty description is technically valid (Pydantic allows it)"""
        # Note: This tests Pydantic's default behavior. Applications may want to add custom validation.
        config = ToolConfig(
            id="test_tool",
            description="",
            transport="stdio",
            command="python",
        )
        assert config.description == ""

    # Tests for ToolConfigTransport enum type
    def test_transport_field_accepts_enum_value(self):
        """Test that transport field accepts ToolConfigTransport enum values"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.STDIO,
            command="python",
        )
        assert config.transport == ToolConfigTransport.STDIO
        assert config.transport.value == "stdio"

    def test_transport_field_accepts_string_value(self):
        """Test that transport field accepts string values (backward compatibility)"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport="stdio",
            command="python",
        )
        # Pydantic should coerce string to enum
        assert config.transport == ToolConfigTransport.STDIO
        assert isinstance(config.transport, ToolConfigTransport)

    def test_all_transport_enum_values(self):
        """Test that all ToolConfigTransport enum values work correctly"""
        for transport_enum in ToolConfigTransport:
            config = ToolConfig(
                id="test_tool",
                description="Test tool",
                transport=transport_enum,
                url="http://localhost:8000"
                if transport_enum != ToolConfigTransport.STDIO
                else None,
                command="python"
                if transport_enum == ToolConfigTransport.STDIO
                else None,
            )
            assert config.transport == transport_enum
            assert isinstance(config.transport, ToolConfigTransport)

    def test_transport_enum_values_match_expected(self):
        """Test that ToolConfigTransport enum has expected values"""
        assert ToolConfigTransport.STDIO.value == "stdio"
        assert ToolConfigTransport.SSE.value == "sse"
        assert ToolConfigTransport.STREAMABLE_HTTP.value == "streamable_http"

    def test_serialization_with_enum_transport(self):
        """Test model_dump serialization with ToolConfigTransport enum"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.SSE,
            url="http://localhost:8000/sse",
        )
        dumped = config.model_dump()
        # Enum should be serialized to its string value
        assert dumped["transport"] == "sse"
        assert isinstance(dumped["transport"], str)

    def test_serialization_with_mode_json(self):
        """Test model_dump with mode='json' serialization"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.STREAMABLE_HTTP,
            url="http://localhost:8000",
        )
        dumped = config.model_dump(mode="json")
        # Enum should be serialized to its string value in JSON mode
        assert dumped["transport"] == "streamable_http"
        assert isinstance(dumped["transport"], str)

    def test_deserialization_with_enum_transport(self):
        """Test model_validate deserialization with ToolConfigTransport enum"""
        data = {
            "id": "test_tool",
            "description": "Test tool",
            "transport": ToolConfigTransport.STDIO,
            "command": "python",
        }
        config = ToolConfig.model_validate(data)
        assert config.transport == ToolConfigTransport.STDIO
        assert isinstance(config.transport, ToolConfigTransport)

    def test_deserialization_with_string_transport(self):
        """Test model_validate deserialization with string transport value"""
        data = {
            "id": "test_tool",
            "description": "Test tool",
            "transport": "sse",
            "url": "http://localhost:8000/sse",
        }
        config = ToolConfig.model_validate(data)
        # String should be coerced to enum
        assert config.transport == ToolConfigTransport.SSE
        assert isinstance(config.transport, ToolConfigTransport)

    def test_json_deserialization_with_string_transport(self):
        """Test model_validate_json deserialization with string transport"""
        json_str = json.dumps(
            {
                "id": "test_tool",
                "description": "Test tool",
                "transport": "streamable_http",
                "url": "http://localhost:8000",
            }
        )
        config = ToolConfig.model_validate_json(json_str)
        assert config.transport == ToolConfigTransport.STREAMABLE_HTTP
        assert isinstance(config.transport, ToolConfigTransport)

    def test_roundtrip_serialization_deserialization(self):
        """Test that serialization and deserialization roundtrip correctly"""
        original = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.SSE,
            url="http://localhost:8000/sse",
        )
        # Serialize to dict
        dumped = original.model_dump()
        # Deserialize back
        restored = ToolConfig.model_validate(dumped)
        assert restored.transport == original.transport
        assert restored.id == original.id
        assert restored.description == original.description
        assert restored.url == original.url

    def test_roundtrip_json_serialization(self):
        """Test that JSON serialization and deserialization roundtrip correctly"""
        original = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.STDIO,
            command="python",
            args=["script.py"],
        )
        # Serialize to JSON string
        json_str = original.model_dump_json()
        # Deserialize back
        restored = ToolConfig.model_validate_json(json_str)
        assert restored.transport == original.transport
        assert restored.id == original.id
        assert restored.description == original.description
        assert restored.command == original.command
        assert restored.args == original.args

    def test_invalid_transport_enum_value(self):
        """Test that invalid transport value raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ToolConfig(
                id="test_tool",
                description="Test tool",
                transport="invalid_transport_value",
                command="python",
            )
        assert "transport" in str(exc_info.value)

    def test_transport_enum_comparison(self):
        """Test that transport enum values can be compared correctly"""
        config1 = ToolConfig(
            id="tool1",
            description="Tool 1",
            transport=ToolConfigTransport.STDIO,
            command="python",
        )
        config2 = ToolConfig(
            id="tool2",
            description="Tool 2",
            transport=ToolConfigTransport.STDIO,
            command="python",
        )
        config3 = ToolConfig(
            id="tool3",
            description="Tool 3",
            transport=ToolConfigTransport.SSE,
            url="http://localhost:8000",
        )
        assert config1.transport == config2.transport
        assert config1.transport != config3.transport

    def test_transport_enum_in_conditional(self):
        """Test that transport enum can be used in conditionals"""
        config = ToolConfig(
            id="test_tool",
            description="Test tool",
            transport=ToolConfigTransport.STDIO,
            command="python",
        )
        # Test enum comparison in conditional
        if config.transport == ToolConfigTransport.STDIO:
            assert True
        else:
            assert False, "Transport enum comparison failed"

        # Test enum value comparison
        if config.transport.value == "stdio":
            assert True
        else:
            assert False, "Transport enum value comparison failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
