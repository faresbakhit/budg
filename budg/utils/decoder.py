import json
import tomllib
from typing import Any, Protocol, TypeAlias

from budg.utils.types import SupportsRead

DecoderError: TypeAlias = ValueError


class Decoder(Protocol):
    name: str
    extensions: tuple[str]

    @staticmethod
    def load(fp: SupportsRead[bytes], /) -> dict[str, Any]:
        ...


class TOMLDecoder(Decoder):
    name = "toml"
    extensions = (".toml",)

    @staticmethod
    def load(fp: SupportsRead[bytes]) -> dict[str, Any]:
        return tomllib.load(fp)


class JSONDecoder(Decoder):
    name = "json"
    extensions = (".json",)

    @staticmethod
    def load(fp: SupportsRead[bytes]) -> dict[str, Any]:
        data: dict[str, Any] | Any = json.load(fp)
        if not isinstance(data, dict):
            raise json.JSONDecodeError("Expecting object", "", 0)
        return data
