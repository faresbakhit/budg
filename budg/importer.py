import importlib
from typing import Any


class ImportFromStringError(ValueError):
    pass


def import_from_string(import_str: str) -> Any:
    mod, _, attrs = import_str.partition(":")

    if not mod or not attrs:
        msg = "import string '{}' must be in format '<module>:<object>[.<attribute>]*'."
        raise ImportFromStringError(msg.format(import_str))

    try:
        instance: Any = importlib.import_module(mod)
    except ModuleNotFoundError:
        msg = "module '{}' not found."
        raise ImportFromStringError(msg.format(mod)) from None

    for nested_attr in attrs.split("."):
        try:
            instance = getattr(instance, nested_attr)
        except AttributeError:
            if instance.__name__ == mod:
                msg = "module '{}' has no attribute '{}'."
            else:
                msg = f"object '{instance.__name__}' in '{{}}' has no attribute '{{}}'."
            raise ImportFromStringError(msg.format(mod, nested_attr)) from None

    return instance


def object_name_from_import_string(import_str: str) -> str:
    return import_str.partition(":")[2].rsplit(".", maxsplit=1)[-1]
