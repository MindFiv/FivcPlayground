"""
Tests for AgentRunContent images and files fields.

Covers:
- Repository persistence roundtrip (FileAgentRunRepository)
- JSON file contents on disk verification
- ChatMessage rendering (mocked Streamlit)
"""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from fivcplayground.agents.types import AgentRun, AgentRunContent, AgentRunStatus
from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
from fivcplayground.labs.components.chat_message import ChatMessage
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


# --- Chat Message Rendering Tests ---


class TestChatMessageImageRendering:
    """Test ChatMessage renders images from AgentRunContent."""

    def test_render_message_with_images_calls_st_image(self):
        """Rendering a message with images should call placeholder.image()."""
        mock_placeholder = Mock()

        content = AgentRunContent(
            text="Here's an image",
            images=[("image/png", base64.b64encode(b"fake-png-data").decode())],
        )

        ChatMessage.render_message(content, mock_placeholder)

        mock_placeholder.image.assert_called_once()

    def test_render_message_with_multiple_images(self):
        """Multiple images should each trigger a placeholder.image() call."""
        mock_placeholder = Mock()

        content = AgentRunContent(
            images=[
                ("image/png", base64.b64encode(b"img1").decode()),
                ("image/jpeg", base64.b64encode(b"img2").decode()),
            ],
        )

        ChatMessage.render_message(content, mock_placeholder)

        assert mock_placeholder.image.call_count == 2

    def test_render_message_no_images_no_st_image_call(self):
        """A message without images should not call placeholder.image()."""
        mock_placeholder = Mock()

        content = AgentRunContent(text="Just text, no images")
        ChatMessage.render_message(content, mock_placeholder)

        mock_placeholder.image.assert_not_called()

    def test_render_message_with_files_shows_expander(self):
        """Rendering a message with files should create an expander."""
        mock_placeholder = Mock()
        mock_expander = MagicMock()
        mock_placeholder.expander.return_value.__enter__ = Mock(
            return_value=mock_expander
        )
        mock_placeholder.expander.return_value.__exit__ = Mock(return_value=False)

        content = AgentRunContent(
            files=[("application/pdf", base64.b64encode(b"pdf-data").decode())],
        )

        ChatMessage.render_message(content, mock_placeholder)

        # Should have created an expander for the file
        mock_placeholder.expander.assert_called()
        expander_call_args = mock_placeholder.expander.call_args
        assert "📎" in expander_call_args[0][0]

    def test_render_message_images_and_text_both_rendered(self):
        """Text and images should both be rendered when present together."""
        mock_placeholder = Mock()

        content = AgentRunContent(
            text="Caption for the image",
            images=[("image/png", base64.b64encode(b"img-data").decode())],
        )

        ChatMessage.render_message(content, mock_placeholder)

        # Both text (via markdown) and image should be rendered
        mock_placeholder.markdown.assert_called()
        mock_placeholder.image.assert_called_once()
