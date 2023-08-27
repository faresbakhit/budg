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
    def __new__(
        cls: type[Self], code: Literal[ExitCode.FAILURE], /, *status: object, sep: str | None = " "
    ) -> "ExitFailureStatus":
        ...

    def __new__(cls: type[Self], code: ExitCode, /, *status: object, sep: str | None = " ") -> Self:
        if not status:
            return ExitStatusCode(code)
        if code == ExitCode.SUCCESS:
            raise ValueError("additional exit status only available for ExitStatus.FAILURE")
        return ExitFailureStatus(*status, sep=sep)


class ExitFailureStatus(str, ExitStatusBuilder):
    FAILURE_STATUS_PREFIX = "error: "

    def __new__(cls, *values: object, sep: str | None = " ") -> Self:
        if sep is None:
            sep = " "
        return super().__new__(cls, sep.join(map(str, values)))

    def __repr__(self) -> str:
        return f"ExitStatus(ExitCode.FAILURE, {self.strip(self.FAILURE_STATUS_PREFIX)!r})"

    def __str__(self) -> str:
        return self.FAILURE_STATUS_PREFIX + self


class ExitStatusCode(int, ExitStatusBuilder):
    def __repr__(self) -> str:
        return f"ExitStatus(ExitCode.{ExitCode(int(self)).name})"


ExitStatus: TypeAlias = ExitStatusCode | ExitFailureStatus
EXIT_SUCCESS = ExitStatusCode(ExitCode.SUCCESS)
