from collections.abc import Sequence
from typing import NoReturn


def main(args: Sequence[str] | None = None) -> NoReturn:
    import os
    import sys

    from budg import cmd

    cwd = os.getcwd()
    if cwd not in sys.path:
        # solve inconsistent behaviour between:
        # - `python -m ....`, assert cwd in sys.path
        # - `console_script`, assert cwd not in sys.path
        # for `budg.utils.importer`
        sys.path.append(cwd)

    cmd.budg.add_command(cmd.build)
    cmd.budg.add_command(cmd.serve)
    cmd.budg.main(args, prog_name="budg")
