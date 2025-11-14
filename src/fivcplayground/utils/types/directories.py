"""
Utility functions for FivcPlayground
"""

import os
from pathlib import Path
from shutil import rmtree
from typing import Optional


class OutputDir(object):
    def __init__(self, base: Optional[str] = None):
        """Create an output directory for FivcPlayground."""
        base = base or os.environ.get(
            "WORKSPACE", os.path.join(os.getcwd(), ".fivcplayground")
        )
        self.base = Path(base)
        self.base = self.base.resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def __str__(self):
        return str(self.base)

    def __enter__(self):
        self._back = os.getcwd()
        os.chdir(str(self))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._back)

    def glob(self, *args, **kwargs):
        return self.base.glob(*args, **kwargs)

    def subdir(self, name: str) -> "OutputDir":
        return OutputDir(os.path.join(str(self), name))

    def cleanup(self, ignore_errors: bool = True):
        rmtree(str(self), ignore_errors=ignore_errors)
