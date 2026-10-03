"""Remove Python caches and local build artifacts (cross-platform)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIR_NAMES = {
    "__pycache__",
    ".benchmarks",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
}

FILE_NAMES = {
    ".coverage",
}


def main() -> None:
    removed = 0

    for name in ("build", "dist"):
        path = ROOT / name
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed += 1

    for path in ROOT.rglob("*"):
        parts = set(path.parts)
        if parts.intersection((".venv", ".tmp", "venv", "node_modules")):
            continue
        if path.is_dir() and path.name in DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
        elif path.is_file() and (
            path.name in FILE_NAMES or path.suffix in (".pyc", ".pyo")
        ):
            path.unlink(missing_ok=True)
            removed += 1

    for path in ROOT.rglob("*"):
        if path.is_dir() and path.name.endswith(".egg-info"):
            parts = set(path.parts)
            if parts.intersection((".venv", ".tmp", "venv", "node_modules")):
                continue
            shutil.rmtree(path, ignore_errors=True)
            removed += 1

    print(f"Cleaned build and cache artifacts ({removed} paths).")


if __name__ == "__main__":
    main()
