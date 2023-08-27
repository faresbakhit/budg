from collections.abc import Mapping
from typing import Any, Protocol, TypeAlias

from budg.utils.types import SupportsRead

DecoderError: TypeAlias = ValueError


class Decoder(Protocol):
    name: str
    extensions: tuple[str]

    @classmethod
    def load(cls, fp: SupportsRead[bytes], /) -> Mapping[str, Any]:
        ...


class TOMLDecoder(Decoder):
    name = "toml"
    extensions = (".toml",)

    @classmethod
    def load(cls, fp: SupportsRead[bytes]) -> Mapping[str, Any]:
        import tomllib

        return tomllib.load(fp)


class JSONDecoder(Decoder):
    name = "json"
    extensions = (".json",)

    @classmethod
    def load(cls, fp: SupportsRead[bytes]) -> Mapping[str, Any]:
        import json

        data: dict[str, Any] | Any = json.load(fp)
        if not isinstance(data, dict):
            raise json.JSONDecodeError("expecting object", "", 0)
        return data
