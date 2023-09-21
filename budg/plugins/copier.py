import shutil
from dataclasses import field
from pathlib import Path

from budg.config import config
from budg.plugins import Plugin, PluginError


@config
class Config:
    pass


@config
class Options:
    directory: str
    destination: str
    ignore: list[str] = field(default_factory=list)
    symlinks_as_is: bool = False
    exist_ok: bool = True


class CopierPlugin(Plugin[Config, Options]):
    def __init__(self, config: Config) -> None:
        self.config = config

    @classmethod
    def get_config_dataclass(cls) -> type[Config]:
        return Config

    @classmethod
    def get_options_dataclass(cls) -> type[Options]:
        return Options

    def build(self, options: Options) -> None:
        ignores = list(map(Path, options.ignore))

        def ignore(src: str, names: list[str]) -> list[str]:
            directory = Path(src).relative_to(options.directory)
            contents = [directory.joinpath(name) for name in names]
            return [p.name for p in contents if p in ignores]

        try:
            shutil.copytree(
                options.directory,
                options.destination,
                ignore=ignore,
                symlinks=options.symlinks_as_is,
                dirs_exist_ok=options.exist_ok,
            )
        except OSError as err:
            raise PluginError(err)
