"""
Tests for AgentRunContent images and files fields.

Covers:
- Repository persistence roundtrip (FileAgentRunRepository)
- JSON file contents on disk verification
"""

import json
import tempfile
from pathlib import Path

import pytest
from fivcplayground.agents.types import AgentRun, AgentRunContent, AgentRunStatus
from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
from fivcplayground.utils import OutputDir


# --- Persistence Tests ---


class TestImagesFilesPersistence:
    """Test images and files persist correctly through FileAgentRunRepository."""

    @pytest.mark.asyncio
    async def test_file_repository_images_round_trip(self):
        """Images in reply should survive save-and-retrieve through the repository."""
        with tempfile.TemporaryDirectory() as tmp_path:
            repo = FileAgentRunRepository(OutputDir(tmp_path))
            session_id = "test-session"

            agent_run = AgentRun(
                agent_id="painter",
                status=AgentRunStatus.COMPLETED,
                reply=AgentRunContent(
                    text="Here is your image",
                    images=[("image/png", "aGVsbG8="), ("image/jpeg", "d29ybGQ=")],
                ),
            )
            await repo.update_agent_run_async(session_id, agent_run)
            retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

            assert retrieved.reply is not None
            assert retrieved.reply.images is not None
            assert len(retrieved.reply.images) == 2
            assert retrieved.reply.images[0] == ("image/png", "aGVsbG8=")
            assert retrieved.reply.images[1] == ("image/jpeg", "d29ybGQ=")

    @pytest.mark.asyncio
    async def test_file_repository_files_round_trip(self):
        """Files in reply should survive save-and-retrieve through the repository."""
        with tempfile.TemporaryDirectory() as tmp_path:
            repo = FileAgentRunRepository(OutputDir(tmp_path))
            session_id = "test-session"

            agent_run = AgentRun(
                agent_id="filebot",
                status=AgentRunStatus.COMPLETED,
                reply=AgentRunContent(
                    text="Here is your file",
                    files=[("application/pdf", "cGRmY29udGVudA==")],
                ),
            )
            await repo.update_agent_run_async(session_id, agent_run)
            retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

            assert retrieved.reply is not None
            assert retrieved.reply.files is not None
            assert len(retrieved.reply.files) == 1
            assert retrieved.reply.files[0] == ("application/pdf", "cGRmY29udGVudA==")

    @pytest.mark.asyncio
    async def test_file_repository_json_file_contains_images(self):
        """The JSON file on disk should contain the images field as a list of 2-element arrays."""
        with tempfile.TemporaryDirectory() as tmp_path:
            repo = FileAgentRunRepository(OutputDir(tmp_path))
            session_id = "test-session"

            agent_run = AgentRun(
                agent_id="painter",
                status=AgentRunStatus.COMPLETED,
                reply=AgentRunContent(
                    images=[("image/png", "aGVsbG8=")],
                ),
            )
            await repo.update_agent_run_async(session_id, agent_run)

            # Find and read the JSON file on disk
            run_files = list(Path(tmp_path).rglob(f"*{agent_run.id}.json"))
            assert len(run_files) == 1
            with open(run_files[0], "r") as f:
                data = json.load(f)

            assert data["reply"]["images"] == [["image/png", "aGVsbG8="]]

    @pytest.mark.asyncio
    async def test_delta_with_images_not_persisted_by_repository(self):
        """delta.images must be excluded from persistence (delta has exclude=True)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            repo = FileAgentRunRepository(OutputDir(tmp_path))
            session_id = "test-session"

            agent_run = AgentRun(
                agent_id="painter",
                delta=AgentRunContent(images=[("image/png", "aGVsbG8=")]),
            )
            await repo.update_agent_run_async(session_id, agent_run)
            retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

            assert retrieved.delta is None

    @pytest.mark.asyncio
    async def test_mixed_content_round_trip(self):
        """Content with text, structured, images, and files all survive persistence."""
        with tempfile.TemporaryDirectory() as tmp_path:
            repo = FileAgentRunRepository(OutputDir(tmp_path))
            session_id = "test-session"

            agent_run = AgentRun(
                agent_id="multimodal",
                status=AgentRunStatus.COMPLETED,
                reply=AgentRunContent(
                    text="Multi-modal response",
                    structured={"answer": 42},
                    images=[("image/webp", "d2VicA==")],
                    files=[("text/csv", "Y3N2")],
                ),
            )
            await repo.update_agent_run_async(session_id, agent_run)
            retrieved = await repo.get_agent_run_async(session_id, agent_run.id)

            assert retrieved.reply.text == "Multi-modal response"
            assert retrieved.reply.structured == {"answer": 42}
            assert retrieved.reply.images[0] == ("image/webp", "d2VicA==")
            assert retrieved.reply.files[0] == ("text/csv", "Y3N2")
