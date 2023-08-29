import getopt
import os
import sys
from typing import TextIO

import budg
from budg.config import ConfigLoaderError, load_config
from budg.exit import EXIT_SUCCESS, ExitFailureStatus, ExitStatus
from budg.utils.decoder import Decoder, JSONDecoder, TOMLDecoder

AVAILABLE_DECODERS_LIST: list[type[Decoder]] = [TOMLDecoder, JSONDecoder]
AVAILABLE_DECODERS = {decoder.name: decoder for decoder in AVAILABLE_DECODERS_LIST}

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
                output.write(HELP)
                return EXIT_SUCCESS
            case "-V" | "--version":
                output.write(budg.version + "\n")
                return EXIT_SUCCESS
            case _:
                pass

    try:
        config = load_config(
            config_from=config_from,
            config_format=config_format,
            default_decoder=TOMLDecoder,
            available_decoders=AVAILABLE_DECODERS,
            path_template="./config{}",
            from_import=True,
        )
    except ConfigLoaderError as exc:
        return ExitFailureStatus(exc)

    print(config)

    # try:
    #     plugins = config.budg.transform_plugins()
    # except (ImportFromStringError, DataclassFromDictError) as exc:
    #     return ExitFailureStatus(f"'{config_file}': {exc}")

    # for no, rule in enumerate(config.budg.rules):
    #     try:
    #         plugin = plugins[rule.plugin]
    #     except KeyError:
    #         msg = f"{config_file}: budg.rules[{no}].plugin: plugin with name '{rule.plugin}' not set"
    #         return ExitFailureStatus(msg)
    #     options_dataclass = plugin.get_options_dataclass()
    #     try:
    #         options = dataclass_from_dict(options_dataclass, rule.options)
    #     except DataclassFromDictError as exc:
    #         return ExitFailureStatus(f"{config_file}: budg.rules[{no}].options: {exc}")
    #     plugin.build(options)

    return EXIT_SUCCESS
