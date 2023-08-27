from dataclasses import dataclass, field
from typing import Any

from budg.plugins import Plugin
from budg.utils.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.utils.exceptions import NotSubclassError
from budg.utils.importer import (
    ImportFromStringError,
    import_from_string,
    object_name_from_import_string,
)

config = dataclass(frozen=True, kw_only=True, slots=True)


@config
class BudgConfigPlugin:
    source: str
    config: dict[str, Any]

    def to_plugin(self) -> Plugin[Any, Any]:
        obj = import_from_string(self.source)
        if not issubclass(obj, Plugin):
            raise NotSubclassError("must be a sub-class of 'budg.plugins.Plugin'")
        try:
            config_dataclass: Any = obj.get_config_dataclass()
        except NotImplementedError as exc:
            raise ImportFromStringError(exc)
        config = dataclass_from_dict(config_dataclass, self.config)
        try:
            instance: Plugin[Any, Any] = obj(config)
        except TypeError as exc:
            raise ImportFromStringError(exc)
        return instance


@config
class BudgConfigRule:
    plugin: str
    options: dict[str, Any]


@config
class BudgConfig:
    rules: list[BudgConfigRule]
    plugins: dict[str, BudgConfigPlugin] = field(default_factory=dict)

    def transform_plugins(self) -> dict[str, Plugin[Any, Any]]:
        d: dict[str, Plugin[Any, Any]] = {}
        for name, config_plugin in self.plugins.items():
            try:
                d[name] = config_plugin.to_plugin()
            except ImportFromStringError as exc:
                raise ImportFromStringError(f"budg.plugins.{name}.plugin: {exc}")
            except NotSubclassError as exc:
                objname = object_name_from_import_string(config_plugin.source)
                raise ImportFromStringError(f"budg.plugins.{name}.plugin: '{objname}' {exc}")
            except DataclassFromDictError as exc:
                raise DataclassFromDictError(f"budg.plugins.{name}.config: {exc}")
        return d


@config
class Config:
    budg: BudgConfig = field(default_factory=BudgConfig)
