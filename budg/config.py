from dataclasses import dataclass, field

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
