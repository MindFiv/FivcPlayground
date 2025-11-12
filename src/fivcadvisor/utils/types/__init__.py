"""
Types module for FivcAdvisor utils.

This module provides core utility types and abstract base classes:
- OutputDir: Context manager for managing output directories
- LazyValue: Lazy-evaluated transparent proxy for deferred computation
- Runnable: Abstract base class for objects supporting sync and async execution
- RunnableMonitor: Abstract base class for monitoring runnable execution
"""

__all__ = [
    "OutputDir",
    "Runnable",
    "ProxyRunnable",
    "LazyValue",
]

from .directories import OutputDir
from .runnables import Runnable, ProxyRunnable
from .variables import LazyValue
