import json
import tomllib
import typing as t

DecoderError: t.TypeAlias = ValueError


class Decoder(t.Protocol):
    name: str
    extensions: tuple[str]

    @staticmethod
    def load(fp: t.BinaryIO, /) -> dict[str, t.Any]:
        ...


class TOMLDecoder(Decoder):
    name = "toml"
    extensions = (".toml",)

    @staticmethod
    def load(fp: t.BinaryIO) -> dict[str, t.Any]:
        return tomllib.load(fp)


class JSONDecoder(Decoder):
    name = "json"
    extensions = (".json",)

    @staticmethod
    def load(fp: t.BinaryIO) -> dict[str, t.Any]:
        data: dict[str, t.Any] | t.Any = json.load(fp)
        if not isinstance(data, dict):
            raise json.JSONDecodeError("Expecting object", "", 0)
        return data
