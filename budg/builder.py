from dataclasses import dataclass
from typing import Any

from budg.plugins import Plugin


@dataclass(frozen=True, kw_only=True, slots=True)
class BuilderRule:
    plugin: str
    options: dict[str, Any]


def build(
    plugins: dict[str, Plugin[Any, Any]],
    rules: list[BuilderRule],
) -> None:
    pass
