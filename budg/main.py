import typing as t


def main(args: t.Sequence[str] | None = None) -> t.NoReturn:
    from budg import cmd

    cmd.budg.add_command(cmd.build)
    cmd.budg.add_command(cmd.serve)
    cmd.budg.main(args, prog_name="Budg")
