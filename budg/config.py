import inspect
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import budg
from budg.plugins import Plugin
from budg.utils.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.utils.decoder import Decoder, DecoderError
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
        config = dataclass_from_dict(self.config, config_dataclass)
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
                raise ImportFromStringError(
                    f"budg.plugins.{name}.plugin: '{objname}' {exc}"
                )
            except DataclassFromDictError as exc:
                raise DataclassFromDictError(f"budg.plugins.{name}.config: {exc}")
        return d


@config
class Config:
    budg: BudgConfig = field(default_factory=BudgConfig)


class ConfigLoaderError(Exception):
    pass


def load_config(
    *,
    config_from: str | None = None,
    config_format: str | None = None,
    default_decoder: type[Decoder],
    available_decoders: dict[str, type[Decoder]],
    path_template: str,
    from_import: bool = False,
) -> Config:
    if from_import and config_from is not None and ":" in config_from:
        try:
            obj = import_from_string(config_from)
        except ImportFromStringError as exc:
            raise ConfigLoaderError(f"'{config_from}': {exc}")
        # `obj.__name__` not guaranteed to exist
        name = object_name_from_import_string(config_from)
        try:
            parameters = inspect.signature(obj).parameters
            if len(parameters) != 1:
                raise TypeError
            param = next(iter(parameters.values()))
            if param.kind == param.KEYWORD_ONLY:
                raise TypeError
        except TypeError:
            msg = "object '{}' must be of type '{}'"
            msg = msg.format(name, "(tuple[int, int, int]) -> Mapping[str, Any]")
            raise ConfigLoaderError(msg) from None
        data: Any | Mapping[str, Any] = obj(budg.__version_info__)
        # `dataclass_from_dict` shouldn't complain about non-str keys
        if not isinstance(data, Mapping):
            msg = "return value of '{}()' is not a 'Mapping'"
            raise ConfigLoaderError(msg.format(name))
        return dataclass_from_dict(data, Config)

    def determine_config() -> tuple[str, type[Decoder]]:
        for decoder in available_decoders.values():
            for ext in decoder.extensions:
                config_path = path_template.format(ext)
                if os.path.exists(config_path):
                    return config_path, decoder
        config_path = path_template.format(default_decoder.default_extension)
        return (config_path, default_decoder)

    decoder = default_decoder

    if config_format is not None:
        decoder = available_decoders[config_format]
        if config_from is None:
            config_from = path_template.format(decoder.default_extension)
    elif config_from is None:
        config_from, decoder = determine_config()
        config_format = decoder.name

    if config_format is None:
        for dec in available_decoders.values():
            if config_from.endswith(dec.extensions):
                decoder = dec

    try:
        with open(config_from, "rb") as fp:
            data = decoder.load(fp)
            return dataclass_from_dict(data, Config)
    except OSError as exc:
        raise ConfigLoaderError(f"'{config_from}': {exc.strerror}")
    except DecoderError as exc:
        raise ConfigLoaderError(f"'{config_from}': {decoder.name}: {exc}")
    except DataclassFromDictError as exc:
        raise ConfigLoaderError(f"'{config_from}': {exc}")
