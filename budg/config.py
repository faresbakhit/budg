from __future__ import annotations

import inspect
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import budg
from budg.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.decoders import Decoder, DecoderError
from budg.importer import (
    ImportFromStringError,
    import_from_string,
    object_name_from_import_string,
)
from budg.plugins import Plugin

config = dataclass(frozen=True)


@config
class BudgConfigDependency:
    source: str
    config: dict[str, Any]

    def to_plugin(self) -> Plugin[Any, Any]:
        try:
            obj = import_from_string(self.source)
        except ImportFromStringError as exc:
            raise PluginTransformerError(exc)
        if not issubclass(obj, Plugin):
            msg = "must be a sub-class of 'budg.plugins.Plugin'"
            raise PluginTransformerError(msg)
        try:
            config_dataclass: Any = obj.get_config_dataclass()
        except NotImplementedError as exc:
            raise PluginTransformerError(exc)
        try:
            config = dataclass_from_dict(self.config, config_dataclass, strict=True)
        except DataclassFromDictError as exc:
            raise PluginTransformerConfigError(exc)
        instance: Plugin[Any, Any] = obj(config)
        return instance


@config
class BuilderRule:
    plugin: str
    options: dict[str, Any]


@config
class BudgConfig:
    rules: list[BuilderRule]
    dependencies: dict[str, BudgConfigDependency]

    def transform_plugins(self) -> dict[str, Plugin[Any, Any]]:
        d: dict[str, Plugin[Any, Any]] = {}
        for name, dependency in self.dependencies.items():
            try:
                d[name] = dependency.to_plugin()
            except PluginTransformerConfigError as exc:
                msg = "budg.plugins.{}.config: {}"
                raise PluginTransformerConfigError(msg.format(name, exc)) from None
            except PluginTransformerError as exc:
                msg = "budg.plugins.{}.source: {}"
                raise PluginTransformerConfigError(msg.format(name, exc)) from None
        return d


@config
class Config:
    source: str
    budg: BudgConfig


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
        data = {"source": config_from, **data}
        return dataclass_from_dict(data, Config)

    def determine_config() -> tuple[str, type[Decoder]]:
        for decoder in available_decoders.values():
            for ext in decoder.extensions:
                config_path = path_template.format(ext=ext)
                if os.path.exists(config_path):
                    return config_path, decoder
        config_path = path_template.format(ext=default_decoder.get_default_extension())
        return (config_path, default_decoder)

    decoder = default_decoder

    if config_format is not None:
        decoder = available_decoders[config_format]
        if config_from is None:
            config_from = path_template.format(ext=decoder.get_default_extension())
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
            data = {"source": config_from, **data}
            return dataclass_from_dict(data, Config)
    except OSError as exc:
        raise ConfigLoaderError(f"'{config_from}': {exc.strerror}")
    except DecoderError as exc:
        raise ConfigLoaderError(f"'{config_from}': {decoder.name}: {exc}")
    except DataclassFromDictError as exc:
        raise ConfigLoaderError(f"'{config_from}': {exc}")


class ConfigLoaderError(Exception):
    pass


class PluginTransformerError(Exception):
    pass


class PluginTransformerConfigError(PluginTransformerError):
    pass
