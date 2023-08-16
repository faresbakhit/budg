from enum import IntEnum
from typing import Literal, Self, TypeAlias, overload


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class ExitStatusBuilder:
    @overload
    def __new__(cls: type[Self], code: ExitCode, /) -> "ExitStatusCode":
        ...

    @overload
    def __new__(cls: type[Self], code: Literal[ExitCode.FAILURE], status: str, /) -> "ExitFailureStatus":
        ...

    def __new__(cls: type[Self], code: ExitCode, status: str | None = None, /) -> Self:
        if status is None:
            return ExitStatusCode(code)
        if code == ExitCode.SUCCESS:
            raise ValueError("additional exit status only available for ExitStatus.FAILURE")
        return ExitFailureStatus(status)


class ExitFailureStatus(str, ExitStatusBuilder):
    FAILURE_STATUS_PREFIX = "error: "

    def __new__(cls: type[Self], status: str) -> Self:
        return super().__new__(cls, f"{cls.FAILURE_STATUS_PREFIX}{status}")

    def __repr__(self) -> str:
        return f"ExitStatus(ExitCode.FAILURE, {self.strip(self.FAILURE_STATUS_PREFIX)!r})"


class ExitStatusCode(int, ExitStatusBuilder):
    def __new__(cls: type[Self], code: ExitCode) -> Self:
        return super().__new__(cls, code)

    def __repr__(self) -> str:
        return f"ExitStatus(ExitCode.{ExitCode(self).name})"


ExitStatus: TypeAlias = ExitStatusCode | ExitFailureStatus
