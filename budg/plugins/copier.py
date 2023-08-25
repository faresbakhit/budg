from budg.config import config
from budg.plugins import BasePlugin
from budg.utils.classproperty import classproperty


@config
class Config:
    pass


class CopierPlugin(BasePlugin[Config]):
    def __init__(self, config: Config) -> None:
        self.config = config

    @classproperty
    def config_dataclass(cls) -> type[Config]:
        return Config
