"""
Shell tool for executing system commands following Strands framework patterns.

This module provides shell command execution capabilities with proper error handling,
timeout support, and comprehensive documentation aligned with Strands framework conventions.

Supported operations:
    - shell: Execute shell commands with timeout and working directory support
"""

import json
import subprocess
from typing import Optional


def shell(
    command: str,
    timeout: int = 30,
    cwd: Optional[str] = None,
    structured: bool = False,
) -> str:
    """
    Execute a shell command and return its output.

    Executes a shell command with a timeout and returns the output. The working
    directory can be optionally specified and is validated before execution.
    All errors are returned as error messages rather than raising exceptions.

    Args:
        command: Shell command to execute (e.g., "ls -la", "echo 'Hello'")
        timeout: Maximum time in seconds to wait for command completion (default: 30)
        cwd: Working directory for command execution (default: current directory)
        structured: If True, return JSON with stdout, stderr, and exit_code fields.
                   If False (default), return combined stdout + stderr as plain string.

    Returns:
        str: If structured=False: Command output (stdout + stderr combined) or error
             message prefixed with "Error:" if the operation fails.
             If structured=True: JSON string with keys "stdout", "stderr", and
             "exit_code", or error message prefixed with "Error:" if the operation fails.

    Raises:
        No exceptions are raised. All errors are returned as error messages.

    Examples:
        >>> shell("echo 'Hello, World!'")
        'Hello, World!'
        >>> shell("ls -la /tmp")
        'total 48\\ndrwxrwxrwt...'
        >>> shell("sleep 60", timeout=1)
        'Error: Command timed out after 1 seconds'
        >>> shell("ls /nonexistent")
        'Error: ls: cannot access /nonexistent: No such file or directory'
        >>> shell("echo 'test'", structured=True)
        '{"stdout": "test\\n", "stderr": "", "exit_code": 0}'
    """
    try:
        # Validate working directory if provided
        if cwd:
            from pathlib import Path

            cwd_path = Path(cwd).resolve()
            if not cwd_path.exists():
                return f"Error: Working directory not found: {cwd}"
            if not cwd_path.is_dir():
                return f"Error: Path is not a directory: {cwd}"
            cwd = str(cwd_path)

        # Execute command with timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        # Return output in requested format
        if structured:
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
            return json.dumps(output, indent=2)
        else:
            # Return combined output (stdout + stderr)
            output = result.stdout
            if result.stderr:
                output += result.stderr

            return (
                output
                if output
                else f"Command executed successfully (exit code: {result.returncode})"
            )

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: Shell command not found or invalid"
    except PermissionError:
        return "Error: Permission denied executing command"
    except Exception as e:
        return f"Error: {str(e)}"
