from dataclasses import dataclass, field

from dacite import from_dict as config_from_dict

__all__ = [
    "config_from_dict",
    "BaseConfig",
    "BudgConfig",
    "BudgDirectoriesConfig",
]

dataclass = dataclass(frozen=True, kw_only=True, slots=True)


@dataclass
class BudgDirectoriesConfig:
    templates: str = "./layouts"
    sources: str = "./content"
    statics: str = "./public"
    build: str = "./dist"


@dataclass
class BudgConfig:
    directories: BudgDirectoriesConfig = field(default_factory=BudgDirectoriesConfig)


@dataclass
class BaseConfig:
    budg: BudgConfig = field(default_factory=BudgConfig)
