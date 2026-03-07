"""Type argument aliases for path types."""

from __future__ import annotations

from pathlib import Path, PurePath

from everybase import Arg


__all__ = [
    "PathArg",
]

type PathArg = Arg[Path | PurePath | str]
