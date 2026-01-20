"""Path args."""

from __future__ import annotations

from pathlib import Path, PurePath

from every.ergs import Arg


__all__ = [
    "PathArg",
]

type PathArg = Arg[Path | PurePath]
