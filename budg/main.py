import getopt
import inspect
import os
import sys
from collections.abc import Mapping, MutableMapping
from typing import Any, TextIO

import budg
from budg.config import Config
from budg.exit import EXIT_SUCCESS, ExitFailureStatus, ExitStatus
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


def determine_config() -> tuple[str, type[Decoder]]:
    for decoder in AVAILABLE_DECODERS.values():
        for ext in decoder.extensions:
            config_path = CONFIG_PATH_TEMPLATE.format(ext=ext)
            if os.path.exists(config_path):
                return config_path, decoder
    return (DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_DECODER)


def config_from_file(file: str | None = None, format: str | None = None) -> tuple[str, Mapping[str, Any]]:
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
        with open(file, "rb") as fp:
            return file, decoder.load(fp)
    except OSError as exc:
        raise OSError(f"{file!r}: {exc.strerror}")
    except DecoderError as exc:
        raise DecoderError(f"{file!r}: {decoder.name}: {exc}")


def config_from_import(import_str: str) -> Mapping[str, Any]:
    obj = import_from_string(import_str)
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
        msg = "object '{name}' must be of type '{type}'"
        raise ImportFromStringError(msg.format(name=name, type="(tuple[int, int, int]) -> Mapping[str, Any]"))
    # `dataclass_from_dict` shouldn't complain about non-str keys
    ret: Any | MutableMapping[str, Any] = obj(budg.__version_info__)
    if not isinstance(ret, MutableMapping):
        msg = "return value of '{name}()' is not a 'Mapping'"
        raise ImportFromStringError(msg.format(name=name))
    return ret


USAGE = "Usage: budg [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]..."
HELP = f"""{USAGE}

  The Modern and Extensible Static Site Generator

Options:
  --config [PATH|IMPORT]  Site configurations from file or funcion import.
                          [default: ./config.toml]
  --config-format         Site configurations file format.  [default: toml]
  --version               Show the version and exit.
  --help                  Show this message and exit.

Commands:
  build  Compile a static site as defined by a config file
  serve  Launch a web server for the build output directory
"""


def main(args: list[str] | None = None, output: TextIO | None = None) -> ExitStatus:
    if args is None:
        args = sys.argv[1:]

    if output is None:
        output = sys.stdout

    cwd = os.getcwd()
    if cwd not in sys.path:
        # solve inconsistent behaviour between:
        # - `python -m ....`, assert cwd in sys.path
        # - `console_script`, assert cwd not in sys.path
        # for `budg.utils.importer`
        sys.path.append(cwd)

    try:
        opts, _ = getopt.getopt(
            args,
            "hv",
            [
                "config=",
                "config-format=",
                "version",
                "help",
            ],
        )
    except getopt.GetoptError as exc:
        help = "Try 'budg --help' for more information."
        return ExitFailureStatus(exc, USAGE, help, sep="\n")

    config_file = None
    config_format = None
    for opt, val in opts:
        if opt == "--config":
            config_file = val
        elif opt == "--config-format":
            val = val.lower()
            if val not in AVAILABLE_DECODERS:
                formats_list = [*AVAILABLE_DECODERS]
                formats = ", ".join(map(repr, formats_list[:-1]))
                if len(formats_list) > 1:
                    formats += f", and {formats_list[-1]!r}"
                return ExitFailureStatus(f"--config-format '{val}': available formats are {formats}.")
            config_format = val
        elif opt in ("-h", "--help"):
            output.write(HELP)
            return EXIT_SUCCESS
        elif opt in ("-v", "--version"):
            output.write(budg.version + "\n")
            return EXIT_SUCCESS

    if config_file is not None and ":" in config_file:
        try:
            data = config_from_import(config_file)
        except ImportFromStringError as exc:
            return ExitFailureStatus(f"'{config_file}': {exc}")
    else:
        try:
            config_file, data = config_from_file(config_file, config_format)
        except (OSError, DecoderError) as exc:
            return ExitFailureStatus(exc)

    try:
        config = dataclass_from_dict(Config, data)
    except DataclassFromDictError as exc:
        return ExitFailureStatus(f"'{config_file}': {exc}")

    try:
        plugins = config.budg.transform_plugins()
    except (ImportFromStringError, DataclassFromDictError) as exc:
        return ExitFailureStatus(f"'{config_file}': {exc}")

    for no, rule in enumerate(config.budg.rules):
        try:
            plugin = plugins[rule.plugin]
        except KeyError:
            msg = f"{config_file}: budg.rules[{no}].plugin: plugin with name '{rule.plugin}' not set"
            return ExitFailureStatus(msg)
        options_dataclass = plugin.get_options_dataclass()
        try:
            options = dataclass_from_dict(options_dataclass, rule.options)
        except DataclassFromDictError as exc:
            return ExitFailureStatus(f"{config_file}: budg.rules[{no}].options: {exc}")
        plugin.build(options)

    return EXIT_SUCCESS
