"""Path type for Shape system.

Provides PathType, PathRef, and PathSlot for working with
Python pathlib.Path objects.

Example:
    from everybase.type import PathSlot

    class Config(Shape):
        config_file = PathSlot()
        data_dir = PathSlot()

    # Operations
    Config.config_file.set(Path("/etc/app/config.json"))
    Config.config_file.get().parent()
"""

from __future__ import annotations

from .args import PathArg
from .ref import PathRef
from .slot import PathSlot
from .type import PathType


__all__ = [
    "PathType",
    "PathRef",
    "PathSlot",
    "PathArg",
]
