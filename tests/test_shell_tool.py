"""
Tests for the shell tools module.

Tests verify:
- shell with various shell commands
- shell with structured=True for structured output
- Error handling for invalid commands and directories
- Timeout handling for long-running commands
"""

import json
import pytest
import tempfile

from fivcplayground.tools.shell import shell

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


class TestShell:
    """Test shell function."""

    def test_simple_echo_command(self):
        """Test simple echo command."""
        result = shell("echo 'Hello, World!'")
        assert "Hello, World!" in result

    def test_command_with_exit_code(self):
        """Test command execution returns output."""
        result = shell("echo 'test'")
        assert isinstance(result, str)
        assert "test" in result

    def test_command_with_stderr(self):
        """Test command that produces stderr."""
        # Using a command that will produce stderr
        result = shell("ls /nonexistent_directory_12345 2>&1")
        assert isinstance(result, str)

    def test_command_with_custom_cwd(self):
        """Test command execution with custom working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = shell("pwd", cwd=tmpdir)
            assert tmpdir in result or "successfully" in result.lower()

    def test_invalid_cwd(self):
        """Test command with invalid working directory."""
        result = shell("echo test", cwd="/nonexistent_path_12345")
        assert "Error" in result
        assert "not found" in result.lower()

    def test_command_timeout(self):
        """Test command timeout handling."""
        # Use a command that will timeout
        result = shell("sleep 60", timeout=1)
        assert "Error" in result
        assert "timed out" in result.lower()

    def test_returns_string(self):
        """Test that shell always returns a string."""
        result = shell("echo 'test'")
        assert isinstance(result, str)


class TestShellStructured:
    """Test shell function with structured=True parameter."""

    def test_structured_output_format(self):
        """Test structured output with stdout, stderr, exit_code."""
        result = shell("echo 'test'", structured=True)
        assert isinstance(result, str)
        data = json.loads(result)
        assert "stdout" in data
        assert "stderr" in data
        assert "exit_code" in data

    def test_successful_command_output(self):
        """Test successful command returns exit code 0."""
        result = shell("echo 'success'", structured=True)
        data = json.loads(result)
        assert data["exit_code"] == 0
        assert "success" in data["stdout"]

    def test_command_with_custom_cwd(self):
        """Test command with custom working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = shell("pwd", cwd=tmpdir, structured=True)
            data = json.loads(result)
            assert data["exit_code"] == 0

    def test_invalid_cwd(self):
        """Test command with invalid working directory."""
        result = shell("echo test", cwd="/nonexistent_path_12345", structured=True)
        assert "Error" in result

    def test_command_timeout(self):
        """Test command timeout handling."""
        result = shell("sleep 60", timeout=1, structured=True)
        assert "Error" in result
        assert "timed out" in result.lower()

    def test_returns_json_string(self):
        """Test that output is valid JSON."""
        result = shell("echo 'test'", structured=True)
        assert isinstance(result, str)
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)


class TestShellToolIntegration:
    """Integration tests for shell tools."""

    def test_all_output_formats_return_strings(self):
        """Test that shell returns strings in both formats."""
        assert isinstance(shell("echo test"), str)
        assert isinstance(shell("echo test", structured=True), str)

    @pytest.mark.skipif(not AVAILABLE_BACKENDS, reason="No backends available")
    @pytest.mark.parametrize("BackendClass", AVAILABLE_BACKENDS)
    def test_shell_tool_creation(self, BackendClass):
        """Test that shell can be wrapped as a tool."""
        backend = BackendClass()
        wrapped_tool = backend.create_tool(shell)
        assert wrapped_tool.name is not None
        assert wrapped_tool.description is not None

    @pytest.mark.skipif(not AVAILABLE_BACKENDS, reason="No backends available")
    @pytest.mark.parametrize("BackendClass", AVAILABLE_BACKENDS)
    def test_shell_structured_parameter(self, BackendClass):
        """Test that shell with structured=True parameter works correctly."""
        backend = BackendClass()
        wrapped_tool = backend.create_tool(
            lambda cmd: shell(cmd, structured=True),
            tool_name="shell_structured",
            tool_description="Execute shell command with structured output",
        )
        assert wrapped_tool.name is not None
        assert wrapped_tool.description is not None
