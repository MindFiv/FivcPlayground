#!/usr/bin/env python3
"""
Tests for ChromaTextSplitter class.

Tests verify:
- Basic text splitting with various chunk sizes
- Chunk overlap functionality
- Recursive splitting by separators (paragraph, line, space, character)
- Edge cases (empty text, very long words, etc.)
- Semantic structure preservation
"""

from fivcplayground.backends.chroma.splitters import ChromaTextSplitter


class TestChromaTextSplitterBasic:
    """Test basic text splitting functionality."""

    def test_initialization_with_defaults(self):
        """Test ChromaTextSplitter initialization with default parameters."""
        splitter = ChromaTextSplitter()
        assert splitter.chunk_size == 1000
        assert splitter.chunk_overlap == 50
        assert splitter.separators == ["\n\n", "\n", " ", ""]

    def test_initialization_with_custom_params(self):
        """Test ChromaTextSplitter initialization with custom parameters."""
        splitter = ChromaTextSplitter(
            chunk_size=500, chunk_overlap=100, separators=["\n", " ", ""]
        )
        assert splitter.chunk_size == 500
        assert splitter.chunk_overlap == 100
        assert splitter.separators == ["\n", " ", ""]

    def test_split_empty_text(self):
        """Test splitting empty text."""
        splitter = ChromaTextSplitter(chunk_size=100)
        result = splitter.split_text("")
        assert result == []

    def test_split_text_smaller_than_chunk_size(self):
        """Test splitting text smaller than chunk size."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "This is a short text."
        result = splitter.split_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_split_by_paragraph_breaks(self):
        """Test splitting by paragraph breaks (\\n\\n)."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = splitter.split_text(text)
        assert len(result) >= 1
        # Each paragraph should be preserved
        assert "First paragraph." in " ".join(result)
        assert "Second paragraph." in " ".join(result)

    def test_split_by_line_breaks(self):
        """Test splitting by line breaks (\\n) when paragraphs are too large."""
        splitter = ChromaTextSplitter(chunk_size=50)
        text = "Line one is quite long and will exceed the chunk size.\nLine two is also long.\nLine three."
        result = splitter.split_text(text)
        assert len(result) > 1
        # All chunks should be <= chunk_size
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size

    def test_split_by_spaces(self):
        """Test splitting by spaces when lines are too large."""
        splitter = ChromaTextSplitter(chunk_size=30)
        text = "This is a very long sentence that will need to be split by spaces"
        result = splitter.split_text(text)
        assert len(result) > 1
        # All chunks should be <= chunk_size
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size

    def test_chunk_size_respected(self):
        """Test that all chunks respect the chunk_size limit."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "This is a long text. " * 50  # Create a long text
        result = splitter.split_text(text)
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size


class TestChromaTextSplitterOverlap:
    """Test chunk overlap functionality."""

    def test_chunk_overlap_zero(self):
        """Test splitting with no overlap."""
        splitter = ChromaTextSplitter(chunk_size=50, chunk_overlap=0)
        text = "word " * 30  # 150 characters
        result = splitter.split_text(text)
        # With no overlap, chunks should not repeat content
        combined = "".join(result)
        # The combined text should be similar in length to original
        assert len(combined) >= len(text) - 10  # Allow small difference

    def test_chunk_overlap_nonzero(self):
        """Test splitting with overlap."""
        splitter = ChromaTextSplitter(chunk_size=100, chunk_overlap=20)
        text = "word " * 50  # 250 characters
        result = splitter.split_text(text)
        assert len(result) > 1
        # All chunks should respect size limit
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size


class TestChromaTextSplitterEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_very_long_word(self):
        """Test splitting text with a single very long word."""
        splitter = ChromaTextSplitter(chunk_size=50)
        text = "a" * 100  # Single word longer than chunk_size
        result = splitter.split_text(text)
        # Should still split the word
        assert len(result) > 0
        # At least one chunk should be the max size
        assert any(len(chunk) == splitter.chunk_size for chunk in result)

    def test_multiple_consecutive_separators(self):
        """Test text with multiple consecutive separators."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "Para 1\n\n\n\nPara 2\n\n\n\nPara 3"
        result = splitter.split_text(text)
        assert len(result) > 0
        # Should handle multiple separators gracefully

    def test_mixed_separators(self):
        """Test text with mixed separator types."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "Para 1\n\nLine 1\nLine 2\nWord1 Word2 Word3\n\nPara 2"
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size

    def test_text_with_special_characters(self):
        """Test text with special characters."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "Hello! @#$%^&*() World? [brackets] {braces} <tags>"
        result = splitter.split_text(text)
        assert len(result) > 0
        # All special characters should be preserved
        combined = "".join(result)
        assert "@#$%^&*()" in combined
        assert "[brackets]" in combined

    def test_unicode_text(self):
        """Test splitting unicode text."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "Hello 世界 مرحبا мир 🌍 " * 10
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size


class TestChromaTextSplitterRealWorldScenarios:
    """Test real-world text splitting scenarios."""

    def test_split_markdown_document(self):
        """Test splitting a markdown-like document."""
        splitter = ChromaTextSplitter(chunk_size=200)
        text = """# Title

This is the introduction paragraph.

## Section 1

Content for section 1 goes here.

## Section 2

Content for section 2 goes here.

### Subsection 2.1

More detailed content here."""
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size

    def test_split_code_block(self):
        """Test splitting code-like text."""
        splitter = ChromaTextSplitter(chunk_size=150)
        text = """def hello_world():
    print("Hello, World!")
    return True

def goodbye_world():
    print("Goodbye, World!")
    return False"""
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size

    def test_split_paul_graham_essay(self):
        """Test splitting with real essay text (from LangChain docs)."""
        splitter = ChromaTextSplitter(chunk_size=100, chunk_overlap=0)
        text = """What I Worked On

February 2021

Before college the two main things I worked on, outside of school, were writing and programming. I didn't write essays. I wrote what beginning writers were supposed to write then, and probably still are: short stories. My stories were awful. They had hardly any plot, just characters with strong feelings, which I imagined made them deep.

The first programs I tried writing were on the IBM 1401 that our school district used for what was then called "data processing." This was in 9th grade, so I was 13 or 14."""
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size
        # Verify content is preserved
        combined = "".join(result)
        assert "What I Worked On" in combined
        assert "February 2021" in combined


class TestChromaTextSplitterConsistency:
    """Test consistency and determinism of splitting."""

    def test_split_consistency(self):
        """Test that splitting the same text produces the same result."""
        splitter = ChromaTextSplitter(chunk_size=100)
        text = "This is a test. " * 20
        result1 = splitter.split_text(text)
        result2 = splitter.split_text(text)
        assert result1 == result2

    def test_split_with_different_separators(self):
        """Test splitting with custom separators."""
        text = "Part1|Part2|Part3|Part4"
        splitter = ChromaTextSplitter(chunk_size=50, separators=["|", " ", ""])
        result = splitter.split_text(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk) <= splitter.chunk_size
