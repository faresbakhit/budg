import os
import platform
import typing as t

import click

from budg import VERSION
from budg.config import BaseConfig
from budg.utils.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.utils.decoder import Decoder, DecoderError, JSONDecoder, TOMLDecoder

AVAILABLE_CONFIG_DECODERS: dict[str, type[Decoder]] = {
    decoder.name: decoder
    for decoder in [
        TOMLDecoder,
        JSONDecoder,
    ]
}
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
    for decoder in AVAILABLE_CONFIG_DECODERS.values():
        for ext in decoder.extensions:
            config_path = CONFIG_PATH_TEMPLATE.format(ext=ext)
            if os.path.exists(config_path):
                return config_path, decoder
    return (DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_DECODER)


@click.group(chain=True)
@click.version_option(VERSION, message=VERSION_INFO_MESSAGE)
@click.option(
    "--config",
    default=None,
    type=click.Path(allow_dash=True),
    help=f"Site configurations file.  [default: {DEFAULT_CONFIG_PATH}]",
)
@click.option(
    "--config-format",
    default=None,
    type=click.Choice([*AVAILABLE_CONFIG_DECODERS], case_sensitive=False),
    help=f"Site configurations file format. [default: {DEFAULT_CONFIG_DECODER.name}]",
)
@click.pass_context
def budg(ctx: click.Context, config: str | None = None, config_format: str | None = None) -> None:
    """The Modern and Extensible Static Site Generator"""

    guess_format = True
    decoder = DEFAULT_CONFIG_DECODER

    if config_format is not None:
        guess_format = False
        decoder = AVAILABLE_CONFIG_DECODERS[config_format]
        if config is None:
            config = CONFIG_PATH_TEMPLATE.format(ext=decoder.extensions[0])

    if config is None:
        guess_format = False
        config, decoder = determine_config()

    if guess_format:
        for format in AVAILABLE_CONFIG_DECODERS.values():
            if config.endswith(format.extensions):
                decoder = format

    try:
        with click.open_file(config, "rb") as fp:
            fp = t.cast(t.BinaryIO, fp)
            data = decoder.load(fp)
    except DecoderError as exc:
        raise click.ClickException(f"{config!r}: {decoder.name}: {exc}")
    except OSError as exc:
        raise click.ClickException(f"{config!r}: {exc.strerror}")

    try:
        ctx.obj = dataclass_from_dict(BaseConfig, data)
    except DataclassFromDictError as exc:
        raise click.ClickException(f"{config!r}: {exc}")
