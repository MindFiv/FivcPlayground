import functools
import importlib
from typing import Any


def _load_dotted_attribute(dotpath: str) -> tuple[str, str, Any]:
    if "." not in dotpath:
        raise ValueError(
            f"Invalid dotted path '{dotpath}': must contain at least one dot "
            "separating module path from attribute name."
        )
    module_path, attr_name = dotpath.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return module_path, attr_name, getattr(module, attr_name)


class DynamicCallable(object):
    """A callable or class dynamically loaded from a dotted import path.

    The underlying function is resolved at construction time.
    Function metadata (__name__, __doc__, etc.) is copied via functools.update_wrapper
    so function-backed instances are transparent to tool decorators.

    Raises:
        ValueError: If dotpath has no dot, or the resolved attribute is not callable.
        ImportError: If the module cannot be imported.
        AttributeError: If the function name doesn't exist on the module.
    """

    def __init__(self, dotpath: str):
        module_path, attr_name, target = _load_dotted_attribute(dotpath)
        if isinstance(target, type):
            self.kind = "class"
            self._callable = target
            self._dotpath = dotpath
            self.__name__ = target.__name__
            self.__doc__ = target.__doc__
            return

        if not callable(target):
            raise ValueError(
                f"'{attr_name}' in module '{module_path}' is not callable."
            )

        self.kind = "function"
        self._callable = target
        self._dotpath = dotpath
        functools.update_wrapper(self, target)

    def __call__(self, *args, **kwargs):
        return self._callable(*args, **kwargs)


DynamicFunc = DynamicCallable
DynamicClass = DynamicCallable
