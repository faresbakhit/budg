"""The Modern and Extensible Static Site Generator

https://github.com/faresbakhit/budg
"""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

import platform

version = "Budg {} ({} {}) [{}-{}]".format(
    __version__,
    platform.python_implementation(),
    platform.python_version(),
    platform.system(),
    platform.machine(),
)
