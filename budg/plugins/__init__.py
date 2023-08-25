from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from budg.utils.classproperty import classproperty

_T_co = TypeVar("_T_co", covariant=True)


class BasePlugin(ABC, Generic[_T_co]):
    @abstractmethod
    def __init__(self, config: _T_co) -> None:
        """Create a new instance of this plugin."""

    @classproperty
    @abstractmethod
    def config_dataclass(cls) -> type[_T_co]:
        """Return the config dataclaass type.

        Plugin implementeres, this function must be marked with `@classproperty`
        from `budg.utils.classproperty`.
        """
