from budg.exit import ExitCode, ExitStatus, ExitStatusBuilder


def main() -> ExitStatus:
    return ExitStatusBuilder(ExitCode.SUCCESS)
