"""
Tests for AgentConfig.response_model property and SchemaConverter integration.

Tests verify:
- Config's JSON Schema converted to Pydantic model via the property
- Returns None when no schema is set
- Auto-generates title when schema lacks one (without mutating original dict)
- jambo SchemaConverter.build() produces valid Pydantic model from JSON Schema
"""

from pydantic import BaseModel

from fivcplayground.agents.types.base import AgentConfig


class TestResponseModelProperty:
    """Tests for AgentConfig.response_model property."""

    def test_config_schema_converted_to_pydantic_model(self):
        """Config's JSON Schema should be converted to Pydantic model."""
        agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
            response_format={
                "title": "TestResponse",
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["answer"],
            },
        )

        result = agent_config.response_model
        assert result is not None
        assert issubclass(result, BaseModel)

        # Verify the model works
        instance = result(answer="hello", confidence=0.9)
        assert instance.answer == "hello"
        assert instance.confidence == 0.9

    def test_returns_none_when_no_schema_set(self):
        """Returns None when no response_format schema is set."""
        agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
        )

        result = agent_config.response_model
        assert result is None

    def test_auto_generates_title_without_mutating_original(self):
        """Schema without title should get auto-generated title without mutating original dict."""
        original_schema = {
            "type": "object",
            "properties": {"result": {"type": "string"}},
        }
        agent_config = AgentConfig(
            id="my-agent",
            model_id="test-model",
            response_format=original_schema,
        )

        result = agent_config.response_model
        assert result is not None
        assert issubclass(result, BaseModel)

        # Verify the original config dict was not mutated
        assert "title" not in agent_config.response_format


class TestSchemaConverterIntegration:
    """Test jambo SchemaConverter.build() produces valid Pydantic models."""

    def test_build_simple_schema(self):
        from jambo import SchemaConverter

        schema = {
            "title": "SimpleModel",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        model_cls = SchemaConverter.build(schema)
        assert issubclass(model_cls, BaseModel)

        instance = model_cls(name="Alice", age=30)
        assert instance.name == "Alice"
        assert instance.age == 30

    def test_build_schema_with_nested_object(self):
        from jambo import SchemaConverter

        schema = {
            "title": "NestedModel",
            "type": "object",
            "properties": {
                "user": {
                    "title": "User",
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                    },
                },
            },
        }

        model_cls = SchemaConverter.build(schema)
        assert issubclass(model_cls, BaseModel)

        instance = model_cls(user={"email": "test@example.com"})
        assert instance.user.email == "test@example.com"
