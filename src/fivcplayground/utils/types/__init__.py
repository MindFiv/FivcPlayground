"""
Types module for FivcPlayground utils.

This module provides core utility types and abstract base classes:
- OutputDir: Context manager for managing output directories
- LazyValue: Lazy-evaluated transparent proxy for deferred computation
"""

__all__ = [
    "DefaultKwargs",
    "OutputDir",
    "DynamicCallable",
    "DynamicClass",
    "DynamicFunc",
    "LazyValue",
]

from .arguments import DefaultKwargs
from .directories import OutputDir
from .callables import DynamicCallable, DynamicClass, DynamicFunc
from .variables import LazyValue
