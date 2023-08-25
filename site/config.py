from collections.abc import Mapping
from typing import Any


def budg(budg_version: tuple[int, int, int]) -> Mapping[str, Any]:
    return {
        "budg": {
            "directories": {
                "budg": f"budg/{'.'.join(map(str, budg_version))}",
            }
        }
    }
