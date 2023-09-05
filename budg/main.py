import getopt
import os
import sys
from typing import TextIO

import budg
from budg.config import ConfigLoaderError, PluginTransformerError, load_config
from budg.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.decoders import Decoder, JSONDecoder, TOMLDecoder
from budg.exit import EXIT_SUCCESS, ExitFailureStatus, ExitStatus

AVAILABLE_DECODERS_LIST: list[type[Decoder]] = [TOMLDecoder, JSONDecoder]
AVAILABLE_DECODERS = {decoder.name: decoder for decoder in AVAILABLE_DECODERS_LIST}

USAGE = "Usage: budg [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]..."
HELP = f"""{USAGE}

  The Modern and Extensible Static Site Generator

Options:
  --config [PATH]  Get configurations from a file or a python-funcion path.
                   [default: ./config.toml]
  --config-format  Format for configurations file.  [default: toml]
  --version        Show the version and exit.
  --help           Show this message and exit.
"""


def main(args: list[str] | None = None, stream: TextIO | None = None) -> ExitStatus:
    if args is None:
        args = sys.argv[1:]

    if stream is None:
        stream = sys.stdout

    cwd = os.getcwd()
    if cwd not in sys.path:
        # solve inconsistent behaviour between:
        # - `python -m ....`, assert cwd in sys.path
        # - `console_script`, assert cwd not in sys.path
        # for `budg.importer`
        sys.path.append(cwd)

    try:
        opts, _ = getopt.getopt(
            args,
            "hV",
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

    config_from = None
    config_format = None
    for opt, val in opts:
        match opt:
            case "--config":
                config_from = val
            case "--config-format":
                val = val.lower()
                if val not in AVAILABLE_DECODERS:
                    fmts = ", ".join(map(repr, AVAILABLE_DECODERS))
                    msg = "option --config-format={}: available formats are {}"
                    return ExitFailureStatus(msg.format(val, fmts))
                config_format = val
            case "-h" | "--help":
                stream.write(HELP)
                return EXIT_SUCCESS
            case "-V" | "--version":
                stream.write(budg.version + "\n")
                return EXIT_SUCCESS
            case _:
                pass

    try:
        config = load_config(
            config_from=config_from,
            config_format=config_format,
            default_decoder=TOMLDecoder,
            available_decoders=AVAILABLE_DECODERS,
            path_template="./config{ext}",
            from_import=True,
        )
    except ConfigLoaderError as exc:
        return ExitFailureStatus(exc)

    try:
        plugins = config.budg.transform_plugins()
    except PluginTransformerError as exc:
        return ExitFailureStatus(f"'{config.source}': {exc}")

    for no, rule in enumerate(config.budg.rules):
        try:
            plugin = plugins[rule.plugin]
        except KeyError:
            msg = "{}: budg.rules[{}].plugin: plugin with name '{}' not set"
            return ExitFailureStatus(msg.format(config.source, no, rule.plugin))
        options_dataclass = plugin.get_options_dataclass()
        try:
            options = dataclass_from_dict(rule.options, options_dataclass, strict=True)
        except DataclassFromDictError as exc:
            msg = "{}: budg.rules[{}].options: {}"
            return ExitFailureStatus(msg.format(config.source, no, exc))
        plugin.build(options)

    return EXIT_SUCCESS
