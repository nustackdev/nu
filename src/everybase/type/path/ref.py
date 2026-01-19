"""Path Ref."""

from __future__ import annotations

from pathlib import Path, PurePath

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.types import BoolType, StrType

from .args import PathArg
from .type import PathType


__all__ = [
    "PathRef",
]


class PathRef(CollectionItemRefBase[Path, PathType], PrimitiveRef):
    """Reference to a Path value in storage."""

    def set(self, value: PathArg) -> PathType:
        """Set the Path value."""
        if isinstance(value, (Path, PurePath)):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return PathType(TypedSetCmd(self, val))

    def get(self) -> PathType:
        """Get the Path value."""
        return PathType.from_str(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def name(self) -> StrType:
        return self.get().name()

    def stem(self) -> StrType:
        return self.get().stem()

    def suffix(self) -> StrType:
        return self.get().suffix()

    # Note: parent() conflicts with Ref's parent()

    def exists(self) -> BoolType:
        return self.get().exists()

    def is_file(self) -> BoolType:
        return self.get().is_file()

    def is_dir(self) -> BoolType:
        return self.get().is_dir()

    def is_absolute(self) -> BoolType:
        return self.get().is_absolute()

    def as_posix(self) -> StrType:
        return self.get().as_posix()

    def as_uri(self) -> StrType:
        return self.get().as_uri()
