from __future__ import annotations

from enum import IntEnum
from typing import Union


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class ExitStatusBuilder:
    def __new__(  # type: ignore[misc]
        cls,
        code: ExitCode,
        /,
        *status: object,
        sep: str | None = " ",
    ) -> "ExitStatus":
        if not status:
            return ExitStatusCode(code)
        if code == ExitCode.SUCCESS:
            msg = "additional exit status not available for ExitCode.SUCCESS"
            raise ValueError(msg)
        return ExitFailureStatus(*status, sep=sep)


class ExitFailureStatus(str, ExitStatusBuilder):
    FAILURE_STATUS_PREFIX: str = "error: "

    def __new__(cls, *values: object, sep: str | None = " ") -> "ExitFailureStatus":
        if sep is None:
            sep = " "
        return super().__new__(cls, sep.join(map(str, values)))

    def __repr__(self) -> str:
        s = "ExitStatus(ExitCode.FAILURE, {!r})"
        return s.format(self.strip(self.FAILURE_STATUS_PREFIX))

    def __str__(self) -> str:
        return self.FAILURE_STATUS_PREFIX + self


class ExitStatusCode(int, ExitStatusBuilder):
    def __repr__(self) -> str:
        return f"ExitStatus(ExitCode.{ExitCode(int(self)).name})"


ExitStatus = Union[ExitStatusCode, ExitFailureStatus]
EXIT_SUCCESS = ExitStatusCode(ExitCode.SUCCESS)
