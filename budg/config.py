from dataclasses import dataclass, field

from dacite import from_dict as config_from_dict

__all__ = [
    "config_from_dict",
    "BaseConfig",
    "BudgConfig",
]

dataclass = dataclass(frozen=True, kw_only=True, slots=True)


@dataclass
class BudgRule:
    pass


@dataclass
class BudgConfig:
    directories: dict[str, str] = field(default_factory=dict)
    rules: list[BudgRule] = field(default_factory=list)


@dataclass
class BaseConfig:
    budg: BudgConfig = field(default_factory=BudgConfig)
