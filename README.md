# Budg

A KISS Plugin Based Static Site Generator

> Budg is 1.0! I consider Budg complete and no further improvements will be made to the project. In the case of a very unlikely security vulnerability, please read [SECURITY.md](/SECURITY.md).

- [Extend Budg](#extend-budg)
- [Installation](#installation)

## Extend Budg

Budg is very barebones on its own, the source code is only ~500 LOC with one dependency ([dacite](https://github.com/konradhalas/dacite)), and also one built-in plugin ([copier.py](/budg/plugins/copier.py)).

Users are able to add plugins of their own without changing budg's source code (see the [example](/example/) budgie) but there's still room for improvement:

- Add a new config format (see [decoders.py](/budg/decoders.py))
- Better error messages, maybe colored?
- More built-in plugins

All of that requires modifying Budg's source code so please fork Budg, extend it, patch what you don't like about it and never think about it, the [license](/LICENSE) is [0BSD](https://choosealicense.com/licenses/0bsd/)!

### Development Mode

Create a [virtual environment](https://docs.python.org/3/glossary.html#term-virtual-environment) and use pip's `-e/--editable` flag to install `budg` with the necessary dependencies for development.

```sh
> git clone git@github.com:faresbakhit/budg.git
> python -m venv .venv
# check venv's docs for instructions on how to
# activate the environment in your shell
(.venv) > pip install -e .[dev]
```

## Installation

Budg requires Python 3.8 or later, install with pip:

```sh
> python3 -m pip install budg
> budg --help
```

```text
Usage: budg [OPTIONS]

  A KISS Plugin Based Static Site Generator

Options:
  --config [PATH]  Get configurations from a file or a python-funcion path.
                   [default: ./config.toml]
  --config-format  Format for configurations file.  [default: toml]
  --version        Show the version and exit.
  --help           Show this message and exit.
```
