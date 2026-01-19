"""Path args."""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "PathArg",
]

type PathArg = Arg[Path | PurePath]
