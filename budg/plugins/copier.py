from budg.config import config
from budg.plugins import Plugin


@config
class Config:
    pass


@config
class Options:
    directory: str
    destination: str


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
        print(options)
