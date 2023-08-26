from abc import ABC, abstractmethod
from typing import Generic, TypeVar

_T_CONFIG = TypeVar("_T_CONFIG")
_T_OPTIONS = TypeVar("_T_OPTIONS")

_ABSTRACTCLASSMETHOD_ERR = "{method} in {cls.__name__} is an abstract method"


class Plugin(ABC, Generic[_T_CONFIG, _T_OPTIONS]):
    @abstractmethod
    def __init__(self, config: _T_CONFIG) -> None:
        """Create a new instance of this plugin."""

    @classmethod
    @abstractmethod
    def get_config_dataclass(cls) -> type[_T_CONFIG]:
        """Return the config dataclaass type."""
        msg = _ABSTRACTCLASSMETHOD_ERR.format(cls=cls, method="get_config_dataclass")
        raise NotImplementedError(msg)

    @classmethod
    @abstractmethod
    def get_options_dataclass(cls) -> type[_T_OPTIONS]:
        """Return the options dataclaass type."""
        msg = _ABSTRACTCLASSMETHOD_ERR.format(cls=cls, method="get_options_dataclass")
        raise NotImplementedError(msg)

    @abstractmethod
    def build(self, options: _T_OPTIONS) -> None:
        ...
