import json
import platform
import tomllib
from pathlib import Path

import click

from budg import __version__ as version
from budg.config import BaseConfig, config_from_dict

VERSION_INFO_MESSAGE = "%(prog)s %(version)s ({} {}) [{}-{}]".format(
    platform.python_implementation(),
    platform.python_version(),
    platform.system(),
    platform.machine(),
)


@click.group(chain=True)
@click.version_option(version, message=VERSION_INFO_MESSAGE)
@click.option(
    "--config",
    default=None,
    type=click.Path(
        exists=True,
        dir_okay=False,
        readable=True,
        allow_dash=True,
        path_type=Path,
    ),
    help="Site configurations file.  [default: ./config.toml]",
)
@click.pass_context
def budg(ctx: click.Context, config: Path | None = None) -> None:
    """The Modern and Extensible Static Site Generator"""
    loader = tomllib.load
    decoder_exc = tomllib.TOMLDecodeError

    if config is None:
        config = Path("./config.toml")
        json_config = Path("./config.json")
        if not config.exists() and json_config.exists():
            config = json_config

    if config.suffix == ".json":
        loader = json.load
        decoder_exc = json.JSONDecodeError

    config_file = str(config)

    try:
        with click.open_file(config_file, "rb") as fp:
            data = loader(fp)
    except decoder_exc as err:
        raise click.ClickException(f"{config_file!r}: {err}")
    except OSError as err:
        raise click.ClickException(f"{config_file!r}: {err.strerror}")

    ctx.obj = config_from_dict(BaseConfig, data)
