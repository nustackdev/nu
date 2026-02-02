"""Type argument aliases for path types."""

from __future__ import annotations

from pathlib import Path, PurePath

from everyabc import Arg


__all__ = [
    "PathArg",
]

type PathArg = Arg[Path | PurePath | str]
