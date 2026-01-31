"""Path ref base for filesystem paths.

PathRefBase = RefBase[Path] + Comparable + path operations.
Stored as string for serialization.
"""

from __future__ import annotations

from abc import ABC
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, ListRef, StrRef, TupleRef

    from .args import PathArg
    from .py.refs import PathRef


__all__ = [
    "PathRefBase",
]


class PathRefBase(
    Comparable["Path | PurePath | str | PathRef"],
    RefBase[Path],
    ABC,
):
    """Abstract base for path refs.

    Provides path manipulation operations. Stored as string.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Term[str]) -> PathRef:
        """Create a PathRef from a string."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PathRef

        return PathRef(FuncCallOp(Path, value))

    @classmethod
    def cwd(cls) -> PathRef:
        """Get current working directory."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PathRef

        return PathRef(FuncCallOp(Path.cwd))

    @classmethod
    def home(cls) -> PathRef:
        """Get user home directory."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PathRef

        return PathRef(FuncCallOp(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrRef:
        """Get the final component (filename)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "name"))

    def stem(self) -> StrRef:
        """Get the filename without the final extension."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "stem"))

    def suffix(self) -> StrRef:
        """Get the file extension (including dot)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "suffix"))

    def suffixes(self) -> ListRef:
        """Get all file extensions."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import ListRef

        return ListRef(FuncCallOp(getattr, self, "suffixes"))

    def parent(self) -> PathRef:
        """Get the parent directory."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PathRef

        return PathRef(FuncCallOp(getattr, self, "parent"))

    def root(self) -> StrRef:
        """Get the root (e.g., '/' on Unix)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "root"))

    def anchor(self) -> StrRef:
        """Get the anchor (drive + root)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import StrRef

        return StrRef(FuncCallOp(getattr, self, "anchor"))

    def parts(self) -> TupleRef:
        """Get path parts as a tuple."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import TupleRef

        return TupleRef(FuncCallOp(getattr, self, "parts"))

    def parents(self) -> TupleRef:
        """Get an immutable sequence of parent paths."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import TupleRef

        return TupleRef(FuncCallOp(tuple, FuncCallOp(getattr, self, "parents")))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | str | Term[str]) -> PathRef:
        """Join paths using / operator."""
        from everybase.morphisms import DivOp

        from .py.refs import PathRef

        if isinstance(other, (Path, PurePath)):
            other = PathRef(other)
        return PathRef(DivOp(self, other))

    def joinpath(self, *others: PathArg | str) -> PathRef:
        """Join with multiple path components."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        wrapped = tuple(PathRef(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathRef(MethodCallOp(self, "joinpath", *wrapped))

    def with_name(self, name: str | Term[str]) -> PathRef:
        """Return a new path with the name changed."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        return PathRef(MethodCallOp(self, "with_name", name))

    def with_stem(self, stem: str | Term[str]) -> PathRef:
        """Return a new path with the stem changed."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        return PathRef(MethodCallOp(self, "with_stem", stem))

    def with_suffix(self, suffix: str | Term[str]) -> PathRef:
        """Return a new path with the suffix changed."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        return PathRef(MethodCallOp(self, "with_suffix", suffix))

    def resolve_path(self, strict: bool | Term[bool] = False) -> PathRef:
        """Make the path absolute, resolving symlinks.

        Named resolve_path() to avoid collision with RefBase.resolve().
        """
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        return PathRef(MethodCallOp(self, "resolve", strict))

    def absolute(self) -> PathRef:
        """Make the path absolute (without resolving symlinks)."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        return PathRef(MethodCallOp(self, "absolute"))

    def relative_to(self, other: PathArg | str | Term[str]) -> PathRef:
        """Compute relative path from other."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PathRef

        if isinstance(other, (Path, PurePath)):
            other = PathRef(other)
        return PathRef(MethodCallOp(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolRef:
        """Check if path is absolute."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | str | Term[str]) -> BoolRef:
        """Check if path is relative to other."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        from .py.refs import PathRef

        if isinstance(other, (Path, PurePath)):
            other = PathRef(other)
        return BoolRef(MethodCallOp(self, "is_relative_to", other))

    def match(self, pattern: str | Term[str]) -> BoolRef:
        """Match path against a glob pattern."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolRef:
        """Check if path exists."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "exists"))

    def is_file(self) -> BoolRef:
        """Check if path is a file."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_file"))

    def is_dir(self) -> BoolRef:
        """Check if path is a directory."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_dir"))

    def is_symlink(self) -> BoolRef:
        """Check if path is a symlink."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_symlink"))

    def is_mount(self) -> BoolRef:
        """Check if path is a mount point."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrRef:
        """Return path with forward slashes."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "as_posix"))

    def as_uri(self) -> StrRef:
        """Return path as file:// URI."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "as_uri"))
