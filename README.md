# Budg

The Modern and Extensible Static Site Generator

## Installation

Budg requires Python 3.11 or higher, install with `pip`:

```sh
> python3 -m pip install budg
> budg --version
Budg 0.1.0 (CPython 3.11.3) [Linux-x86_64]
```

## Usage

Check `-h/--help` for build options:

```sh
> budg --help
Usage: budg [OPTIONS]

  The Modern and Extensible Static Site Generator

Options:
  --config [PATH]  Get configurations from a file or a python-funcion path.
                   [default: ./config.toml]
  --config-format  Format for configurations file.  [default: toml]
  --version        Show the version and exit.
  --help           Show this message and exit.
```

Budg can be configured using either a static config file or dynamically from a python function with the format `<module>:<object>[.<attribute>]*` passed to the `--config` option.

The supported formats for a static config file are `toml`, and `json`. The default being `toml` for files 

Example:

```toml
[budg.dependencies]
copier = {source = "budg.plugins.copier:CopierPlugin", config = {}}

[[budg.rules]]
plugin = "copier"
options = {
    directory = "./src/",
    destination = "./dst/"
}
```

## Development Mode

Create a [virtual environment](https://docs.python.org/3/glossary.html#term-virtual-environment) and use pip's `-e/--editable` flag to install `budg` with the necessary dependencies for development:

```sh
> python3 -m venv .venv
> # check venv's docs for instructions on how to
> # activate the environment in your shell
> pip install -e .[dev]
```
