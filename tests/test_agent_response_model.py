"""
Tests for resolve_response_model() helper and SchemaConverter integration.

Tests verify:
- Runtime response_model takes priority over config
- Config's JSON Schema converted to Pydantic model when no runtime model
- Returns None when neither is set
- Auto-generates title when schema lacks one (without mutating original dict)
- jambo SchemaConverter.build() produces valid Pydantic model from JSON Schema
"""

from pydantic import BaseModel

from fivcplayground.agents import resolve_response_model
from fivcplayground.agents.types.base import AgentConfig


class TestResolveResponseModel:
    """Tests for resolve_response_model() helper."""

    def test_runtime_response_model_takes_priority(self):
        """Runtime response_model should take priority over config."""

        class CustomModel(BaseModel):
            custom_field: str

        agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
            response_model={
                "title": "ConfigResponse",
                "type": "object",
                "properties": {"answer": {"type": "string"}},
            },
        )

        result = resolve_response_model(agent_config, response_model=CustomModel)
        assert result is CustomModel

    def test_config_schema_converted_when_no_runtime_model(self):
        """Config's JSON Schema should be converted to Pydantic model when no runtime model."""
        agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
            response_model={
                "title": "TestResponse",
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["answer"],
            },
        )

        result = resolve_response_model(agent_config)
        assert result is not None
        assert issubclass(result, BaseModel)

        # Verify the model works
        instance = result(answer="hello", confidence=0.9)
        assert instance.answer == "hello"
        assert instance.confidence == 0.9

    def test_returns_none_when_neither_set(self):
        """Returns None when neither runtime model nor config schema is set."""
        agent_config = AgentConfig(
            id="test-agent",
            model_id="test-model",
        )

        result = resolve_response_model(agent_config)
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
            response_model=original_schema,
        )

        result = resolve_response_model(agent_config)
        assert result is not None
        assert issubclass(result, BaseModel)

        # Verify the original config dict was not mutated
        assert "title" not in agent_config.response_model


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
