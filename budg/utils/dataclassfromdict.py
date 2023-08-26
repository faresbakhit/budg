from collections.abc import Mapping
from typing import Any, TypeVar

import dacite
from dacite.exceptions import ForwardReferenceError as ForwardReferenceError
from dacite.exceptions import MissingValueError as MissingValueError
from dacite.exceptions import StrictUnionMatchError as StrictUnionMatchError
from dacite.exceptions import UnexpectedDataError as UnexpectedDataError
from dacite.exceptions import UnionMatchError as UnionMatchError
from dacite.exceptions import WrongTypeError as WrongTypeError

__all__ = [
    "dataclass_from_dict",
    "DataclassFromDictError",
    "DataclassFromDictFieldError",
    "ForwardReferenceError",
    "MissingValueError",
    "StrictUnionMatchError",
    "UnexpectedDataError",
    "UnionMatchError",
    "WrongTypeError",
]


DataclassFromDictError = dacite.DaciteError
DataclassFromDictFieldError = dacite.DaciteFieldError


_T = TypeVar("_T")


def dataclass_from_dict(dataclass: type[_T], data: Mapping[str, Any]) -> _T:
    return dacite.from_dict(dataclass, data)
