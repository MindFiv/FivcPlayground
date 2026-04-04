"""
Tests for the filesystem tools module.

Tests verify:
- read_file reads file contents correctly
- write_file creates and writes files
- list_directory lists directory contents
- get_file_info returns file metadata
- create_directory creates directories
- delete_file deletes files
- delete_directory deletes directories
- file_exists checks file/directory existence
- Error handling for invalid paths and permissions
"""

import tempfile
from pathlib import Path

import pytest
from fivcplayground.tools.filesystem import (
    file_read,
    file_search,
    file_write,
)

# Optional backend imports
try:
    from fivcplayground.backends.langchain.tools import LangchainToolBackend

    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    LangchainToolBackend = None

try:
    from fivcplayground.backends.strands.tools import StrandsToolBackend

    HAS_STRANDS = True
except ImportError:
    HAS_STRANDS = False
    StrandsToolBackend = None

# Build list of available backends for parametrize
AVAILABLE_BACKENDS = []
if HAS_LANGCHAIN:
    AVAILABLE_BACKENDS.append(LangchainToolBackend)
if HAS_STRANDS:
    AVAILABLE_BACKENDS.append(StrandsToolBackend)


class TestFileRead:
    """Test file_read function."""

    def test_read_existing_file(self):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello, World!")
            f.flush()
            fname = f.name
        result = file_read(fname)
        assert result == "Hello, World!"
        Path(fname).unlink()

    def test_read_nonexistent_file(self):
        """Test reading a nonexistent file."""
        result = file_read("/nonexistent_file_12345.txt")
        assert "Error" in result
        assert "not found" in result.lower()

    def test_read_directory_as_file(self):
        """Test reading a directory as a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = file_read(tmpdir)
            assert "Error" in result
            assert "not a file" in result.lower()

    def test_read_file_with_encoding(self):
        """Test reading file with specific encoding."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Test content")
            f.flush()
            fname = f.name
        result = file_read(fname, encoding="utf-8")
        assert result == "Test content"
        Path(fname).unlink()

    def test_returns_string(self):
        """Test that file_read returns a string."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            f.flush()
            fname = f.name
        result = file_read(fname)
        assert isinstance(result, str)
        Path(fname).unlink()


class TestFileWrite:
    """Test file_write function."""

    def test_write_new_file(self):
        """Test writing to a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            result = file_write(str(filepath), "Hello, World!")
            assert "Successfully wrote" in result
            assert filepath.exists()
            assert filepath.read_text() == "Hello, World!"

    def test_write_append_mode(self):
        """Test appending to a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("First line\n")
            f.flush()
            fname = f.name
        result = file_write(fname, "Second line\n", mode="append")
        assert "Successfully wrote" in result
        content = Path(fname).read_text()
        assert "First line" in content
        assert "Second line" in content
        Path(fname).unlink()

    def test_write_overwrite_mode(self):
        """Test overwriting a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Original content")
            f.flush()
            fname = f.name
        result = file_write(fname, "New content", mode="write")
        assert "Successfully wrote" in result
        assert Path(fname).read_text() == "New content"
        Path(fname).unlink()

    def test_write_creates_parent_directories(self):
        """Test that file_write creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "test.txt"
            result = file_write(str(filepath), "content")
            assert "Successfully wrote" in result
            assert filepath.exists()

    def test_returns_string(self):
        """Test that file_write returns a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            result = file_write(str(filepath), "test")
            assert isinstance(result, str)


class TestFilesystemToolIntegration:
    """Integration tests for filesystem tools."""

    def test_all_functions_return_strings(self):
        """Test that all functions return strings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert isinstance(file_read(tmpdir), str)
            assert isinstance(file_write(tmpdir + "/test.txt", "test"), str)

    @pytest.mark.skipif(not AVAILABLE_BACKENDS, reason="No backends available")
    @pytest.mark.parametrize("BackendClass", AVAILABLE_BACKENDS)
    def test_file_read_tool_creation(self, BackendClass):
        """Test that file_read can be wrapped as a tool."""
        backend = BackendClass()
        wrapped_tool = backend.create_tool(file_read)
        assert wrapped_tool.name is not None
        assert wrapped_tool.description is not None

    @pytest.mark.skipif(not AVAILABLE_BACKENDS, reason="No backends available")
    @pytest.mark.parametrize("BackendClass", AVAILABLE_BACKENDS)
    def test_file_write_tool_creation(self, BackendClass):
        """Test that file_write can be wrapped as a tool."""
        backend = BackendClass()
        wrapped_tool = backend.create_tool(file_write)
        assert wrapped_tool.name is not None
        assert wrapped_tool.description is not None


class TestFileSearch:
    """Test file_search function."""

    def test_search_basic_pattern(self):
        """Test basic file pattern matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.py").touch()
            Path(tmpdir, "test2.py").touch()
            Path(tmpdir, "readme.txt").touch()

            result = file_search(tmpdir, "*.py")
            assert "test1.py" in result
            assert "test2.py" in result
            assert "readme.txt" not in result
            assert "Found 2 files" in result

    def test_search_no_matches(self):
        """Test when no files match the pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").touch()
            result = file_search(tmpdir, "*.py")
            assert "No items found" in result

    def test_search_nonexistent_directory(self):
        """Test searching in a nonexistent directory."""
        result = file_search("/nonexistent_dir_12345", "*.py")
        assert "Error" in result
        assert "not found" in result.lower()

    def test_search_file_as_directory(self):
        """Test searching when path is a file, not a directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.flush()
            fname = f.name
        result = file_search(fname, "*.py")
        assert "Error" in result
        assert "not a directory" in result.lower()
        Path(fname).unlink()

    def test_search_recursive(self):
        """Test recursive directory search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            Path(tmpdir, "test1.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "test2.py").touch()

            result = file_search(tmpdir, "*.py", recursive=True)
            assert "test1.py" in result
            assert "test2.py" in result
            assert "Found 2 files" in result

    def test_search_non_recursive(self):
        """Test non-recursive directory search (default)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            Path(tmpdir, "test1.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "test2.py").touch()

            result = file_search(tmpdir, "*.py", recursive=False)
            assert "test1.py" in result
            assert "test2.py" not in result
            assert "Found 1 file" in result

    def test_search_max_results(self):
        """Test result limiting with max_results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 test files
            for i in range(10):
                Path(tmpdir, f"test{i}.py").touch()

            result = file_search(tmpdir, "*.py", max_results=3)
            assert "Found 3 files" in result
            assert "limited to 3" in result

    def test_search_complex_pattern(self):
        """Test complex glob patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test_file.py").touch()
            Path(tmpdir, "test_other.py").touch()
            Path(tmpdir, "main.py").touch()

            result = file_search(tmpdir, "test_*.py")
            assert "test_file.py" in result
            assert "test_other.py" in result
            assert "main.py" not in result
            assert "Found 2 files" in result

    def test_search_returns_string(self):
        """Test that file_search returns a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.py").touch()
            result = file_search(tmpdir, "*.py")
            assert isinstance(result, str)

    def test_search_empty_directory(self):
        """Test searching in an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = file_search(tmpdir, "*.py")
            assert "No items found" in result

    def test_search_mixed_file_types(self):
        """Test searching with mixed file types in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "script.py").touch()
            Path(tmpdir, "data.json").touch()
            Path(tmpdir, "readme.md").touch()
            Path(tmpdir, "config.yaml").touch()

            result = file_search(tmpdir, "*.py")
            assert "script.py" in result
            assert "data.json" not in result
            assert "readme.md" not in result
            assert "config.yaml" not in result
            assert "Found 1 file" in result

    def test_search_structured_format(self):
        """Test structured JSON output format."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.py").touch()
            Path(tmpdir, "test2.py").touch()

            result = file_search(tmpdir, "*.py", structured=True)
            # Parse JSON result
            data = json.loads(result)
            assert "items" in data
            assert "count" in data
            assert "truncated" in data
            assert data["count"] == 2
            assert data["truncated"] is False
            assert len(data["items"]) == 2

            # Check file structure
            for file_info in data["items"]:
                assert "path" in file_info
                assert "name" in file_info
                assert "type" in file_info
                assert file_info["type"] == "file"
                assert "size" in file_info

    def test_search_structured_with_metadata(self):
        """Test that structured format includes file metadata."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.py")
            test_file.write_text("print('hello')")

            result = file_search(tmpdir, "*.py", structured=True)
            data = json.loads(result)

            assert len(data["items"]) == 1
            file_info = data["items"][0]
            assert file_info["name"] == "test.py"
            assert file_info["type"] == "file"
            assert file_info["size"] > 0
            assert "test.py" in file_info["path"]

    def test_search_structured_no_matches(self):
        """Test structured format when no files match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").touch()
            result = file_search(tmpdir, "*.py", structured=True)
            # Should return plain text error message, not JSON
            assert "No items found" in result

    def test_search_structured_truncated(self):
        """Test structured format with truncated results."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 5 files
            for i in range(5):
                Path(tmpdir, f"test{i}.py").touch()

            result = file_search(tmpdir, "*.py", structured=True, max_results=3)
            data = json.loads(result)

            assert data["count"] == 3
            assert data["truncated"] is True
            assert data["limit"] == 3
            assert len(data["items"]) == 3

    def test_search_structured_recursive(self):
        """Test structured format with recursive search."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "test2.py").touch()

            result = file_search(tmpdir, "*.py", recursive=True, structured=True)
            data = json.loads(result)

            assert data["count"] == 2
            assert data["truncated"] is False
            assert len(data["items"]) == 2

    def test_search_plain_text_format_default(self):
        """Test that plain text format is default (structured=False)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test1.py").touch()
            Path(tmpdir, "test2.py").touch()

            result = file_search(tmpdir, "*.py", structured=False)
            # Should not be valid JSON
            assert "Found 2 files" in result
            assert "test1.py" in result
            assert "test2.py" in result

    def test_search_structured_error_handling(self):
        """Test that errors are returned as strings, not JSON."""
        result = file_search("/nonexistent", "*.py", structured=True)
        assert "Error" in result
        assert "not found" in result.lower()

    def test_search_include_dirs_false_default(self):
        """Test that directories are excluded by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()

            result = file_search(tmpdir, "*")
            assert "file.py" in result
            assert "subdir" not in result
            assert "Found 1 file" in result

    def test_search_include_dirs_true(self):
        """Test including directories in results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()

            result = file_search(tmpdir, "*", include_dirs=True)
            assert "file.py" in result
            assert "subdir/" in result  # Directory has trailing slash
            assert "Found 1 file, 1 directory" in result

    def test_search_include_dirs_multiple(self):
        """Test including multiple directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.py").touch()
            Path(tmpdir, "file2.py").touch()
            Path(tmpdir, "dir1").mkdir()
            Path(tmpdir, "dir2").mkdir()

            result = file_search(tmpdir, "*", include_dirs=True)
            assert "file1.py" in result
            assert "file2.py" in result
            assert "dir1/" in result
            assert "dir2/" in result
            assert "Found 2 files, 2 directories" in result

    def test_search_include_dirs_structured(self):
        """Test structured format with directories."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.py").touch()
            Path(tmpdir, "subdir").mkdir()

            result = file_search(tmpdir, "*", include_dirs=True, structured=True)
            data = json.loads(result)

            assert "items" in data
            assert data["count"] == 2

            # Check that items have type field
            types = {item["type"] for item in data["items"]}
            assert "file" in types
            assert "directory" in types

            # Check that directory doesn't have size
            for item in data["items"]:
                if item["type"] == "directory":
                    assert "size" not in item
                elif item["type"] == "file":
                    assert "size" in item

    def test_search_include_dirs_structured_no_dirs(self):
        """Test structured format with include_dirs=False."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.py").touch()
            Path(tmpdir, "subdir").mkdir()

            result = file_search(tmpdir, "*", include_dirs=False, structured=True)
            data = json.loads(result)

            assert data["count"] == 1
            assert data["items"][0]["type"] == "file"

    def test_search_include_dirs_recursive(self):
        """Test include_dirs with recursive search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.py").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "file2.py").touch()
            nested = subdir / "nested"
            nested.mkdir()

            result = file_search(tmpdir, "*", recursive=True, include_dirs=True)
            assert "file1.py" in result
            assert "file2.py" in result
            assert "subdir/" in result
            assert "nested/" in result

    def test_search_include_dirs_pattern_matching(self):
        """Test include_dirs with specific patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test_file.py").touch()
            Path(tmpdir, "other.py").touch()
            Path(tmpdir, "test_dir").mkdir()
            Path(tmpdir, "other_dir").mkdir()

            result = file_search(tmpdir, "test_*", include_dirs=True)
            assert "test_file.py" in result
            assert "test_dir/" in result
            assert "other.py" not in result
            assert "other_dir" not in result

    def test_search_include_dirs_plain_text_trailing_slash(self):
        """Test that directories have trailing slash in plain text format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.txt").touch()
            Path(tmpdir, "mydir").mkdir()

            result = file_search(tmpdir, "*", include_dirs=True)
            lines = result.split("\n")

            # Find the directory line
            dir_lines = [ln for ln in lines if "mydir" in ln]
            assert len(dir_lines) > 0
            assert dir_lines[0].endswith("/")

    def test_search_include_dirs_structured_type_field(self):
        """Test that structured format includes type field for all items."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file.py").touch()
            Path(tmpdir, "dir").mkdir()

            result = file_search(tmpdir, "*", include_dirs=True, structured=True)
            data = json.loads(result)

            for item in data["items"]:
                assert "type" in item
                assert item["type"] in ["file", "directory"]

    def test_search_include_dirs_max_results(self):
        """Test max_results with include_dirs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                Path(tmpdir, f"file{i}.py").touch()
            for i in range(3):
                Path(tmpdir, f"dir{i}").mkdir()

            result = file_search(tmpdir, "*", include_dirs=True, max_results=4)
            assert "Found 4 items" not in result  # Should show individual counts
            assert "limited to 4" in result

    @pytest.mark.skipif(not AVAILABLE_BACKENDS, reason="No backends available")
    @pytest.mark.parametrize("BackendClass", AVAILABLE_BACKENDS)
    def test_file_search_tool_creation(self, BackendClass):
        """Test that file_search can be wrapped as a tool."""
        backend = BackendClass()
        wrapped_tool = backend.create_tool(file_search)
        assert wrapped_tool.name is not None
        assert wrapped_tool.description is not None
