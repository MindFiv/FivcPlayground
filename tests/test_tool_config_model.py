#!/usr/bin/env python3
"""
Tests for ToolConfig Pydantic model validation.
"""

import pytest
from pydantic import ValidationError

from fivcplayground.tools.types.base import ToolConfig


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
