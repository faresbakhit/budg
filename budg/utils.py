import typing as t
from collections.abc import Mapping
from os import PathLike

T = t.TypeVar("T")

StrOrBytesPath: t.TypeAlias = str | PathLike[str] | PathLike[bytes]


class EmptyMapping(Mapping[t.Any, t.Any]):
    def __getitem__(self, _: t.Any) -> t.NoReturn:
        raise KeyError

    def get(self, _: t.Any, default: T) -> T:  # type: ignore
        return default

    def __iter__(self) -> t.Iterator[t.Any]:
        yield

    def __len__(self) -> int:
        return 0


EMPTY_MAPPING = EmptyMapping()
