__all__ = [
    "create_default_kwargs",
    "create_lazy_value",
    "create_output_dir",
    "LazyValue",
    "OutputDir",
    "Runnable",
    "ProxyRunnable",
]

from typing import Optional, Callable

from fivcadvisor.utils.types import (
    LazyValue,
    OutputDir,
    Runnable,
    ProxyRunnable,
)


def create_default_kwargs(kwargs: dict, defaults: dict):
    """
    Create default kwargs from a defaults dict.
    """
    for k, v in defaults.items():
        if kwargs.get(k) is None:
            kwargs[k] = v
    return kwargs


def create_lazy_value(getter: Callable):
    """Create a LazyValue proxy from a factory callable."""
    return LazyValue(getter)


def create_output_dir(base: Optional[str] = None):
    """
    Create an output directory for FivcAdvisor.
    """
    return OutputDir(base)
