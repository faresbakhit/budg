import os
import typing as t
from collections.abc import Mapping
from pathlib import Path

from budg.utils import EMPTY_MAPPING, StrOrBytesPath


class BaseConfigError(Exception):
    pass


class ConfigKeyError(BaseConfigError):
    def __init__(self, key: str, *, should_be: str | None = None) -> None:
        self.key = key
        self.should_be = should_be

    def __str__(self) -> str:
        if self.should_be is None:
            return f"Invalid key {self.key!r}"
        return f"Invalid key {self.key!r}: Should be a {self.should_be}"


class BudgConfig:
    def __init__(self, path: StrOrBytesPath, config: dict[str, t.Any]) -> None:
        self.path = Path(os.fsdecode(path))
        self.site = self.path.parent

        options: Mapping[str, t.Any] | t.Any = config.get("options", EMPTY_MAPPING)
        if not isinstance(options, Mapping):
            raise ConfigKeyError("options", should_be="table")

        directories: Mapping[str, t.Any] | t.Any = options.get("directories", EMPTY_MAPPING)
        if not isinstance(directories, Mapping):
            raise ConfigKeyError("directories", should_be="table")

        self.directory = BudgConfigDirectories(directories, parent=self.site)

    def __repr__(self) -> str:
        return "{}(directory={})".format(
            self.__class__.__name__,
            self.directory,
        )


class BudgConfigDirectories:
    def __init__(self, directories: Mapping[str, t.Any], *, parent: Path) -> None:
        layouts = directories.get("layouts", "./layouts")
        pages = directories.get("pages", "./pages")
        public = directories.get("public", "./public")
        build = directories.get("build", "./dist")

        self.layouts = parent.joinpath(layouts)
        self.pages = parent.joinpath(pages)
        self.public = parent.joinpath(public)
        self.build = parent.joinpath(build)

    def __repr__(self) -> str:
        return "{}(layouts={}, pages={}, public={}, build={})".format(
            self.__class__.__name__,
            self.layouts,
            self.pages,
            self.public,
            self.build,
        )
