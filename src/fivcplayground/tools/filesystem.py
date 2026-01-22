"""
Filesystem tools for file operations following Strands framework patterns.

This module provides file reading, writing, and searching capabilities with proper error handling,
type safety, and comprehensive documentation aligned with Strands framework conventions.

Supported operations:
    - file_read: Read file contents with error handling
    - file_write: Write content to files with directory creation
    - file_search: Search for files within a directory using glob patterns
"""

from pathlib import Path


def file_search(
    path: str,
    pattern: str,
    recursive: bool = False,
    max_results: int = 100,
    structured: bool = False,
    include_dirs: bool = False,
) -> str:
    """
    Search for files and optionally directories within a directory using glob patterns.

    Searches a directory for files and/or directories matching the provided glob pattern
    and returns a list of matching paths. Supports both shallow and recursive directory
    traversal. Results are limited to prevent overwhelming output. All errors are
    returned as error messages rather than raising exceptions.

    Args:
        path: Path to the directory to search. Can be relative or absolute.
        pattern: Glob pattern to match files/directories (e.g., "*.py", "test_*.py", "**/*.txt")
        recursive: Whether to search recursively in subdirectories (default: False)
        max_results: Maximum number of matching items to return (default: 100)
        structured: Whether to return results in structured JSON format (default: False)
        include_dirs: Whether to include directories in results (default: False)

    Returns:
        str: Formatted string with matching paths. When structured=False, returns
             one path per line with a summary count. Directories have a trailing slash.
             When structured=True, returns JSON with paths, metadata, and summary.
             Error messages are prefixed with "Error:" in both formats.

    Raises:
        No exceptions are raised. All errors are returned as error messages.

    Examples:
        >>> file_search("/path/to/dir", "*.py")
        '/path/to/dir/file1.py\\n/path/to/dir/file2.py\\n\\nFound 2 files'
        >>> file_search("/path/to/dir", "*", include_dirs=True)
        '/path/to/dir/file1.py\\n/path/to/dir/subdir/\\n\\nFound 1 file, 1 directory'
        >>> file_search("/path/to/dir", "*.py", structured=True)
        '{"items": [{"path": "/path/to/dir/file1.py", "name": "file1.py", "type": "file", "size": 1024}, ...], "count": 2, "truncated": false}'
        >>> file_search("/path/to/dir", "*", include_dirs=True, structured=True)
        '{"items": [{"path": "/path/to/dir/file1.py", "name": "file1.py", "type": "file"}, {"path": "/path/to/dir/subdir", "name": "subdir", "type": "directory"}], "count": 2, "truncated": false}'
        >>> file_search("/nonexistent", "*.py")
        'Error: Directory not found: /nonexistent'
        >>> file_search("/path/to/file.txt", "*.py")
        'Error: Path is not a directory: /path/to/file.txt'
    """
    import json

    try:
        dir_path = Path(path).resolve()

        # Validate path exists
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"

        # Validate path is a directory
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"

        # Search for matching files and/or directories
        matches = []
        try:
            if recursive:
                # Use ** for recursive search
                search_pattern = (
                    f"**/{pattern}" if not pattern.startswith("**") else pattern
                )
                for item_path in dir_path.glob(search_pattern):
                    # Check if we should include this item
                    if item_path.is_file():
                        matches.append((item_path, "file"))
                    elif include_dirs and item_path.is_dir():
                        matches.append((item_path, "directory"))

                    if len(matches) >= max_results:
                        break
            else:
                # Non-recursive search
                for item_path in dir_path.glob(pattern):
                    # Check if we should include this item
                    if item_path.is_file():
                        matches.append((item_path, "file"))
                    elif include_dirs and item_path.is_dir():
                        matches.append((item_path, "directory"))

                    if len(matches) >= max_results:
                        break
        except Exception as e:
            return f"Error: Failed to search directory: {str(e)}"

        # Format results
        if not matches:
            return f"No items found matching pattern: {pattern}"

        match_count = len(matches)
        truncated = match_count >= max_results

        if structured:
            # Return structured JSON format
            items_data = []
            for item_path, item_type in matches:
                try:
                    item_info = {
                        "path": str(item_path),
                        "name": item_path.name,
                        "type": item_type,
                    }

                    # Add size for files
                    if item_type == "file":
                        try:
                            stat_info = item_path.stat()
                            item_info["size"] = stat_info.st_size
                        except Exception:
                            pass

                    items_data.append(item_info)
                except Exception:
                    # If we can't get info, include path, name, and type only
                    items_data.append(
                        {
                            "path": str(item_path),
                            "name": item_path.name,
                            "type": item_type,
                        }
                    )

            result = {
                "items": items_data,
                "count": match_count,
                "truncated": truncated,
            }
            if truncated:
                result["limit"] = max_results

            return json.dumps(result)
        else:
            # Return plain text format
            # Add trailing slash for directories
            formatted_paths = []
            for item_path, item_type in matches:
                if item_type == "directory":
                    formatted_paths.append(str(item_path) + "/")
                else:
                    formatted_paths.append(str(item_path))

            result_text = "\n".join(formatted_paths)

            # Count files and directories for summary
            file_count = sum(1 for _, item_type in matches if item_type == "file")
            dir_count = sum(1 for _, item_type in matches if item_type == "directory")

            # Build summary message
            if include_dirs and dir_count > 0:
                summary = f"\n\nFound {file_count} file{'s' if file_count != 1 else ''}, {dir_count} director{'ies' if dir_count != 1 else 'y'}"
            else:
                summary = (
                    f"\n\nFound {match_count} file{'s' if match_count != 1 else ''}"
                )

            # Add note if results were truncated
            if truncated:
                summary += f" (limited to {max_results})"

            return result_text + summary

    except PermissionError:
        return f"Error: Permission denied accessing directory: {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def file_read(path: str, encoding: str = "utf-8") -> str:
    """
    Read the contents of a file.

    Reads and returns the complete contents of a file with the specified encoding.
    The file path is resolved to an absolute path before reading. All errors are
    returned as error messages rather than raising exceptions.

    Args:
        path: Path to the file to read. Can be relative or absolute.
        encoding: File encoding to use when reading (default: "utf-8")

    Returns:
        str: File contents as a string, or error message prefixed with "Error:"
             if the operation fails.

    Raises:
        No exceptions are raised. All errors are returned as error messages.

    Examples:
        >>> file_read("/path/to/file.txt")
        'File contents here...'
        >>> file_read("/nonexistent.txt")
        'Error: File not found: /nonexistent.txt'
        >>> file_read("/path/to/directory")
        'Error: Path is not a file: /path/to/directory'
    """
    try:
        file_path = Path(path).resolve()

        # Validate path exists
        if not file_path.exists():
            return f"Error: File not found: {path}"

        # Validate path is a file
        if not file_path.is_file():
            return f"Error: Path is not a file: {path}"

        # Read and return file contents
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()

    except PermissionError:
        return f"Error: Permission denied reading file: {path}"
    except UnicodeDecodeError as e:
        return f"Error: Failed to decode file with {encoding} encoding: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def file_write(
    path: str,
    content: str,
    mode: str = "write",
    encoding: str = "utf-8",
) -> str:
    """
    Write content to a file.

    Writes the provided content to a file at the specified path. Creates parent
    directories as needed. Supports both write (overwrite) and append modes.
    All errors are returned as error messages rather than raising exceptions.

    Args:
        path: Path to the file to write. Can be relative or absolute.
        content: Content to write to the file.
        mode: Write mode - "write" to overwrite or "append" to add to end
              (default: "write")
        encoding: File encoding to use when writing (default: "utf-8")

    Returns:
        str: Success message with byte count, or error message prefixed with "Error:"
             if the operation fails.

    Raises:
        No exceptions are raised. All errors are returned as error messages.

    Examples:
        >>> file_write("/path/to/file.txt", "Hello, World!")
        'Successfully wrote 13 bytes to /path/to/file.txt'
        >>> file_write("/path/to/file.txt", "More content", mode="append")
        'Successfully wrote 12 bytes to /path/to/file.txt'
        >>> file_write("/invalid/path/file.txt", "content")
        'Error: Permission denied writing to file: /invalid/path/file.txt'
    """
    try:
        file_path = Path(path).resolve()

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine file mode
        file_mode = "a" if mode == "append" else "w"

        # Write content to file
        with open(file_path, file_mode, encoding=encoding) as f:
            f.write(content)

        return f"Successfully wrote {len(content)} bytes to {path}"

    except PermissionError:
        return f"Error: Permission denied writing to file: {path}"
    except UnicodeEncodeError as e:
        return f"Error: Failed to encode content with {encoding} encoding: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
