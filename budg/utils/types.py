from os import PathLike
from typing import Protocol, TypeAlias, TypeVar

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):
    def read(self, n: int = ..., /) -> _T_co:
        ...


StrPath: TypeAlias = str | PathLike[str]
