from typing import NoReturn, Sequence


def main(args: Sequence[str] | None = None) -> NoReturn:
    from budg import cmd

    cmd.budg.add_command(cmd.build)
    cmd.budg.add_command(cmd.serve)
    cmd.budg.main(args, prog_name=__package__)
