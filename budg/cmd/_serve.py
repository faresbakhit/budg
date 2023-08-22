import click

__all__ = ["serve"]


@click.command()
def serve() -> None:
    """Launch a web server for the build output directory"""
    raise NotImplementedError
