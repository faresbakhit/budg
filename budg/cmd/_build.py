import click
from click.exceptions import ClickException

from budg.config import Config
from budg.utils.dataclassfromdict import DataclassFromDictError, dataclass_from_dict
from budg.utils.importer import ImportFromStringError


@click.command
@click.pass_context
def build(ctx: click.Context) -> None:
    """Compile a static site as defined by a config file"""
    config = ctx.find_object(Config)
    if config is None:
        msg = "{fn}: Object of type '{obj}' not found"
        raise ClickException(msg.format(fn="click.Context.find_object", obj="budg.config.Config"))
    try:
        plugins = config.budg.transform_plugins()
    except (ImportFromStringError, DataclassFromDictError) as exc:
        raise ClickException(f"{config.source}: {exc}")
    for no, rule in enumerate(config.budg.rules):
        try:
            plugin = plugins[rule.plugin]
        except KeyError:
            raise ClickException(f"{config.source}: budg.rules[{no}].plugin: Plugin with name '{rule.plugin}' not set")
        options_dataclass = plugin.get_options_dataclass()
        options = dataclass_from_dict(options_dataclass, rule.options)
        plugin.build(options)
