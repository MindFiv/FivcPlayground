import functools
import importlib


class DynamicFunc(object):
    """A callable that is dynamically loaded from a dotted import path.

    The underlying function is resolved at construction time.
    Function metadata (__name__, __doc__, etc.) is copied via functools.update_wrapper
    so DynamicFunc instances are transparent to tool decorators.

    Raises:
        ValueError: If dotpath has no dot, or the resolved attribute is not callable.
        ImportError: If the module cannot be imported.
        AttributeError: If the function name doesn't exist on the module.
    """

    def __init__(self, dotpath: str):
        if "." not in dotpath:
            raise ValueError(
                f"Invalid dotted path '{dotpath}': must contain at least one dot "
                "separating module path from function name."
            )
        module_path, func_name = dotpath.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        if not callable(func):
            raise ValueError(
                f"'{func_name}' in module '{module_path}' is not callable."
            )
        self._func = func
        self._dotpath = dotpath
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
