import inspect
import os
import platform
from collections.abc import Mapping, MutableMapping
from typing import Any

import click
from click.exceptions import ClickException

from budg import VERSION, VERSION_INFO
from budg.config import Config
from budg.utils.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.utils.decoder import Decoder, DecoderError, JSONDecoder, TOMLDecoder
from budg.utils.importer import (
    ImportFromStringError,
    import_from_string,
    object_name_from_import_string,
)

AVAILABLE_DECODERS_LIST: list[type[Decoder]] = [TOMLDecoder, JSONDecoder]
AVAILABLE_DECODERS = {decoder.name: decoder for decoder in AVAILABLE_DECODERS_LIST}

CONFIG_PATH_TEMPLATE = "./config{ext}"
DEFAULT_CONFIG_PATH = "./config.toml"
DEFAULT_CONFIG_DECODER = TOMLDecoder

VERSION_INFO_MESSAGE = "%(prog)s %(version)s ({} {}) [{}-{}]".format(
    platform.python_implementation(),
    platform.python_version(),
    platform.system(),
    platform.machine(),
)


def determine_config() -> tuple[str, type[Decoder]]:
    for decoder in AVAILABLE_DECODERS.values():
        for ext in decoder.extensions:
            config_path = CONFIG_PATH_TEMPLATE.format(ext=ext)
            if os.path.exists(config_path):
                return config_path, decoder
    return (DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_DECODER)


def config_from_file(file: str | None = None, format: str | None = None) -> Mapping[str, Any]:
    decoder: type[Decoder] = DEFAULT_CONFIG_DECODER

    if format is not None:
        decoder = AVAILABLE_DECODERS[format]
        if file is None:
            file = CONFIG_PATH_TEMPLATE.format(ext=decoder.extensions[0])

    if file is None:
        file, decoder = determine_config()
        format = decoder.name

    if format is None:
        for dec in AVAILABLE_DECODERS.values():
            if file.endswith(dec.extensions):
                decoder = dec

    try:
        with click.open_file(file, "rb") as fp:
            data = decoder.load(fp)
            data["source"] = file
            return data
    except DecoderError as exc:
        raise ClickException(f"{file!r}: {decoder.name}: {exc}")
    except OSError as exc:
        raise ClickException(f"{file!r}: {exc.strerror}")


def config_from_import(import_str: str) -> Mapping[str, Any]:
    excmsg = f"'{import_str}': {{}}"
    try:
        obj = import_from_string(import_str)
    except ImportFromStringError as exc:
        raise ClickException(excmsg.format(exc))
    # `obj.__name__` not guaranteed to exist
    name = object_name_from_import_string(import_str)
    try:
        parameters = inspect.signature(obj).parameters
        if len(parameters) != 1:
            raise TypeError
        param = next(iter(parameters.values()))
        if param.kind == param.KEYWORD_ONLY:
            raise TypeError
    except TypeError:
        msg = excmsg.format("Object '{name}' must be of type '{type}'")
        raise ClickException(msg.format(name=name, type="(tuple[int, int, int]) -> Mapping[str, Any]"))
    # `dataclass_from_dict` shouldn't complain about non-str keys
    ret: Any | MutableMapping[str, Any] = obj(VERSION_INFO)
    if not isinstance(ret, MutableMapping):
        msg = excmsg.format("Return value of '{name}()' is not a 'Mapping'")
        raise ClickException(msg.format(name=name))
    ret["source"] = import_str
    return ret


@click.group(chain=True)
@click.version_option(VERSION, message=VERSION_INFO_MESSAGE)
@click.option(
    "--config",
    default=None,
    type=click.Path(allow_dash=True),
    metavar="[PATH|IMPORT]",
    help=f"Site configurations from file or funcion import.  [default: {DEFAULT_CONFIG_PATH}]",
)
@click.option(
    "--config-format",
    default=None,
    type=click.Choice([*AVAILABLE_DECODERS], case_sensitive=False),
    metavar="",
    help=f"Site configurations file format.  [default: {DEFAULT_CONFIG_DECODER.name}]",
)
@click.pass_context
def budg(ctx: click.Context, config: str | None = None, config_format: str | None = None) -> None:
    """The Modern and Extensible Static Site Generator"""

    if config is not None and ":" in config:
        data = config_from_import(config)
    else:
        data = config_from_file(config, config_format)

    try:
        ctx.obj = dataclass_from_dict(Config, data)
    except DataclassFromDictError as exc:
        raise ClickException(f"{data['source']!r}: {exc}")
