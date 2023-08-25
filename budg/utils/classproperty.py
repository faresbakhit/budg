from typing import Any


class classproperty(property):
    def __get__(self, _: Any, owner: type | None = None, /) -> Any:
        assert self.fget is not None
        return self.fget(owner)
