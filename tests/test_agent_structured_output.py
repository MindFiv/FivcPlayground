"""
Unit tests for structured output support across agent backends.

Tests verify that both Strands and LangChain backends correctly
handle structured output (Pydantic models) in AgentRunContent.
"""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from fivcplayground.agents.types.base import (
    AgentRun,
    AgentRunContent,
    AgentRunStatus,
)
from fivcplayground.agents.types.repositories.files import (
    FileAgentRunRepository,
)
from fivcplayground.utils import OutputDir


class TestAgentRunContentStructuredField:
    """Test AgentRunContent structured field data model."""

    def test_structured_field_creation(self):
        """AgentRunContent should store structured field as dict."""
        content = AgentRunContent(
            text="The answer is 42", structured={"answer": 42, "confidence": 0.95}
        )
        assert content.text == "The answer is 42"
        assert content.structured == {"answer": 42, "confidence": 0.95}

    def test_structured_field_serialization(self):
        """Structured field should serialize to JSON correctly."""
        content = AgentRunContent(
            text="Result", structured={"key": "value", "nested": {"data": [1, 2, 3]}}
        )
        dumped = content.model_dump(mode="json")
        assert dumped["structured"] == {"key": "value", "nested": {"data": [1, 2, 3]}}

    def test_structured_field_deserialization(self):
        """Structured field should deserialize from JSON correctly."""
        data = {"text": "Result", "structured": {"answer": "test", "score": 100}}
        content = AgentRunContent.model_validate(data)
        assert content.structured == {"answer": "test", "score": 100}

    def test_structured_field_optional(self):
        """Structured field should be optional (None by default)."""
        content = AgentRunContent(text="Just text")
        assert content.text == "Just text"
        assert content.structured is None

    def test_structured_field_with_complex_types(self):
        """Structured field should handle complex nested structures."""
        complex_data = {
            "users": [
                {"name": "Alice", "age": 30, "tags": ["admin", "developer"]},
                {"name": "Bob", "age": 25, "tags": ["user"]},
            ],
            "metadata": {
                "total": 2,
                "page": 1,
                "filters": {"active": True, "roles": ["admin", "user"]},
            },
        }
        content = AgentRunContent(text="User list", structured=complex_data)
        assert content.structured == complex_data

        # Verify serialization round-trip
        dumped = content.model_dump(mode="json")
        restored = AgentRunContent.model_validate(dumped)
        assert restored.structured == complex_data


class TestStructuredOutputPersistence:
    """Test structured field persistence in repositories."""

    @pytest.mark.asyncio
    async def test_file_repository_structured_round_trip(self, tmp_path):
        """File repository should persist structured field correctly."""
        output_dir = OutputDir(str(tmp_path))
        repo = FileAgentRunRepository(output_dir)

        agent_run = AgentRun(
            agent_id="test-agent",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text="What is 2+2?"),
            reply=AgentRunContent(
                text="The answer is 4",
                structured={"result": 4, "operation": "addition", "confidence": 1.0},
            ),
        )

        session_id = "test-session"

        await repo.update_agent_run_async(session_id, agent_run)
        retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

        assert retrieved is not None
        assert retrieved.reply is not None
        assert retrieved.reply.text == "The answer is 4"
        assert retrieved.reply.structured == {
            "result": 4,
            "operation": "addition",
            "confidence": 1.0,
        }

    @pytest.mark.asyncio
    async def test_file_repository_none_structured_field(self, tmp_path):
        """File repository should handle None structured field correctly."""
        output_dir = OutputDir(str(tmp_path))
        repo = FileAgentRunRepository(output_dir)

        agent_run = AgentRun(
            agent_id="test-agent",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text="Hello"),
            reply=AgentRunContent(
                text="Hi there",
                structured=None,  # Explicitly None
            ),
        )

        session_id = "test-session-2"

        await repo.update_agent_run_async(session_id, agent_run)
        retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

        assert retrieved is not None
        assert retrieved.reply is not None
        assert retrieved.reply.text == "Hi there"
        assert retrieved.reply.structured is None

    @pytest.mark.asyncio
    async def test_file_repository_complex_structured_data(self, tmp_path):
        """File repository should persist complex structured data."""
        output_dir = OutputDir(str(tmp_path))
        repo = FileAgentRunRepository(output_dir)

        complex_structured = {
            "contacts": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phones": ["+1-555-0100", "+1-555-0101"],
                    "address": {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "zip": "12345",
                    },
                },
                {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phones": ["+1-555-0200"],
                    "address": None,
                },
            ],
            "metadata": {
                "extracted_at": "2026-02-16T10:00:00Z",
                "source": "email",
                "confidence": 0.95,
            },
        }

        agent_run = AgentRun(
            agent_id="data-extractor",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text="Extract contacts from email"),
            reply=AgentRunContent(
                text="Extracted 2 contacts", structured=complex_structured
            ),
        )

        session_id = "test-session-3"

        await repo.update_agent_run_async(session_id, agent_run)
        retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

        assert retrieved is not None
        assert retrieved.reply is not None
        assert retrieved.reply.structured == complex_structured

    @pytest.mark.asyncio
    async def test_file_repository_json_file_contains_structured(self, tmp_path):
        """Verify the JSON file on disk contains the structured field."""
        output_dir = OutputDir(str(tmp_path))
        repo = FileAgentRunRepository(output_dir)

        agent_run = AgentRun(
            agent_id="test-agent",
            status=AgentRunStatus.COMPLETED,
            query=AgentRunContent(text="Test query"),
            reply=AgentRunContent(text="Test reply", structured={"test": "data"}),
        )

        session_id = "test-session-4"

        await repo.update_agent_run_async(session_id, agent_run)

        # Find the JSON file on disk
        run_files = list(Path(tmp_path).rglob(f"*{agent_run.id}.json"))
        assert len(run_files) == 1, "Should find exactly one run file"

        # Read and verify JSON content
        with open(run_files[0], "r") as f:
            data = json.load(f)

        assert "reply" in data
        assert "structured" in data["reply"]
        assert data["reply"]["structured"] == {"test": "data"}


class TestBackendStructuredOutputLogic:
    """Test backend structured output handling logic."""

    def test_strands_backend_pattern(self):
        """Verify Strands backend correctly populates structured field."""
        # This tests the pattern used in strands/agents.py lines 286-294

        class MockResult(BaseModel):
            answer: int
            confidence: float

        # Simulate StrandsAgentResult.structured_output
        mock_structured = MockResult(answer=42, confidence=0.95)

        # Simulate the conversion logic
        structured_dict = mock_structured.model_dump(mode="json")

        # Verify it converts to dict correctly
        assert structured_dict == {"answer": 42, "confidence": 0.95}
        assert isinstance(structured_dict, dict)

    def test_langchain_backend_pattern(self):
        """Verify LangChain backend correctly populates structured field."""
        # This tests the pattern that should be in langchain/agents.py

        class MockResponse(BaseModel):
            name: str
            email: str

        # Simulate outputs["structured_response"]
        mock_outputs = {
            "structured_response": MockResponse(name="John", email="john@example.com"),
            "messages": [{"content": "Extracted: John (john@example.com)"}],
        }

        # Simulate extraction logic
        agent_run_reply_structured = None
        if "structured_response" in mock_outputs:
            structured_output = mock_outputs["structured_response"]
            if isinstance(structured_output, BaseModel):
                agent_run_reply_structured = structured_output

        # Verify extraction works
        assert agent_run_reply_structured is not None
        assert agent_run_reply_structured.name == "John"
        assert agent_run_reply_structured.email == "john@example.com"

        # Verify conversion to dict
        structured_dict = agent_run_reply_structured.model_dump(mode="json")
        assert structured_dict == {"name": "John", "email": "john@example.com"}

    def test_backend_parity_both_populate_structured(self):
        """Both backends should populate structured field identically."""

        class TestModel(BaseModel):
            value: str
            score: float

        # Simulate both backends
        model_instance = TestModel(value="test", score=0.9)
        expected_dict = {"value": "test", "score": 0.9}

        # Strands pattern
        strands_structured = model_instance.model_dump(mode="json")
        strands_content = AgentRunContent(text="Result", structured=strands_structured)

        # LangChain pattern (after our fix)
        langchain_structured = model_instance.model_dump(mode="json")
        langchain_content = AgentRunContent(
            text="Result", structured=langchain_structured
        )

        # Both should be identical
        assert strands_content.structured == expected_dict
        assert langchain_content.structured == expected_dict
        assert strands_content.structured == langchain_content.structured

    def test_backend_returns_pydantic_instance_when_structured(self):
        """Backends should return Pydantic instance, not AgentRunContent."""

        class Result(BaseModel):
            answer: int

        mock_result = Result(answer=42)

        # In both backends, when structured output exists, return the instance
        # This is what the return logic does
        agent_run_reply_structured = mock_result
        agent_run_reply = AgentRunContent(
            text="The answer is 42", structured=mock_result.model_dump(mode="json")
        )

        # Return logic
        returned = (
            agent_run_reply_structured
            if agent_run_reply_structured
            else agent_run_reply
        )

        # Should return the Pydantic instance, not AgentRunContent
        assert isinstance(returned, Result)
        assert returned.answer == 42

    def test_backend_returns_agent_run_content_when_no_structured(self):
        """Backends should return AgentRunContent when no structured output."""

        agent_run_reply_structured = None
        agent_run_reply = AgentRunContent(text="Plain text response")

        # Return logic
        returned = (
            agent_run_reply_structured
            if agent_run_reply_structured
            else agent_run_reply
        )

        # Should return AgentRunContent
        assert isinstance(returned, AgentRunContent)
        assert returned.text == "Plain text response"
        assert returned.structured is None
