import importlib
from typing import Any


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: str) -> Any:
    mod, _, attrs = import_str.partition(":")

    if not mod or not attrs or mod[0] == ".":
        message = "Import string '{import_str}' must be in format '<module>:<object>[.<attribute>]*'."
        raise ImportFromStringError(message.format(import_str=import_str))

    try:
        instance: Any = importlib.import_module(mod)
    except ModuleNotFoundError:
        message = "Module '{mod}' not found."
        raise ImportFromStringError(message.format(mod=mod)) from None

    for nested_attr in attrs.split("."):
        try:
            instance = getattr(instance, nested_attr)
        except AttributeError:
            if instance.__name__ == mod:
                message = "Module '{mod}' has no attribute '{attr}'."
                raise ImportFromStringError(message.format(mod=mod, attr=nested_attr)) from None
            message = "Object '{obj}' in '{mod}' has no attribute '{attr}'."
            raise ImportFromStringError(message.format(obj=instance.__name__, mod=mod, attr=nested_attr)) from None

    return instance
