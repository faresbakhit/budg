import click

from budg.build import BudgBuilder
from budg.config import BudgConfig


@click.command()
@click.pass_context
def build(ctx: click.Context) -> None:
    """Compile a static site as defined by a config file"""
    config = ctx.find_object(BudgConfig)
    if config is None:
        raise click.ClickException("Context not initialized")
    builder = BudgBuilder(config)
    builder.build()
