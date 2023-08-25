from dataclasses import dataclass, field

config = dataclass(frozen=True, kw_only=True, slots=True)


@config
class BudgRule:
    pass


@config
class BudgConfig:
    directories: dict[str, str] = field(default_factory=dict)
    rules: list[BudgRule] = field(default_factory=list)


@config
class BaseConfig:
    budg: BudgConfig = field(default_factory=BudgConfig)
