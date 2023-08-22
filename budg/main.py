import platform
import tomllib
import typing as t
from tomllib import TOMLDecodeError

import click

from budg import __package__ as program
from budg import __version__ as version
from budg.config import BaseConfig, config_from_dict

__all__ = [
    "budg",
    "main",
]

VERSION_INFO_MESSAGE = "%(prog)s %(version)s ({} {}) [{}-{}]".format(
    platform.python_implementation(),
    platform.python_version(),
    platform.system(),
    platform.machine(),
)


@click.group(chain=True)
@click.version_option(version, message=VERSION_INFO_MESSAGE)
@click.option(
    "--config-file",
    default="./config.toml",
    type=click.File("rb"),
    help="Site configurations file.",
    show_default=True,
)
@click.pass_context
def budg(ctx: click.Context, config_file: t.BinaryIO) -> None:
    """The Modern and Extensible Static Site Generator"""
    try:
        data = tomllib.load(config_file)
        ctx.obj = config_from_dict(BaseConfig, data)
    except TOMLDecodeError as err:
        raise click.ClickException(f"Config file {config_file.name!r}: {err}")


def main(args: t.Sequence[str] | None = None) -> t.NoReturn:
    from budg import cmd

    budg.add_command(cmd.build)
    budg.add_command(cmd.serve)
    budg.main(args, prog_name=program)
