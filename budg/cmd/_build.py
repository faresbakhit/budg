import click

from budg.config import BaseConfig

__all__ = ["build"]


@click.command()
@click.pass_context
def build(ctx: click.Context) -> None:
    """Compile a static site as defined by a config file"""
    config = ctx.find_object(BaseConfig)
    if config is None:
        raise click.ClickException("Context not initialized")
    raise NotImplementedError
