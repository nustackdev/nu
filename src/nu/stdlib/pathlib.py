"""Path interface - typed wrapper for pathlib.Path.

_PathI provides path operations (constructors, components, manipulation, tests, conversions, comparison).
PathI is the leaf: _PathI + TypedNu[Path].
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.collections import ListI, TupleI
    from nu.primitives import BoolI, StrI


__all__ = ["PathArg", "PathI"]


type PathArg = Arg[Path | PurePath | str]


class _PathI(Interface):
    """Path operations mixin - constructors, components, manipulation, tests, conversions, comparison."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> PathI:
        """Create a PathI from a string."""
        from nu import FuncCallOp

        return PathI(FuncCallOp(Path, value))

    @classmethod
    def cwd(cls) -> PathI:
        """Get current working directory."""
        from nu import FuncCallOp

        return PathI(FuncCallOp(Path.cwd))

    @classmethod
    def home(cls) -> PathI:
        """Get user home directory."""
        from nu import FuncCallOp

        return PathI(FuncCallOp(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrI:
        """Get the final component (filename)."""
        from nu import FuncCallOp, StrI

        return StrI(FuncCallOp(getattr, self, "name"))

    def stem(self) -> StrI:
        """Get the filename without the final extension."""
        from nu import FuncCallOp, StrI

        return StrI(FuncCallOp(getattr, self, "stem"))

    def suffix(self) -> StrI:
        """Get the file extension (including dot)."""
        from nu import FuncCallOp, StrI

        return StrI(FuncCallOp(getattr, self, "suffix"))

    def suffixes(self) -> ListI:
        """Get all file extensions."""
        from nu import FuncCallOp, ListI

        return ListI(FuncCallOp(getattr, self, "suffixes"))

    def parent(self) -> PathI:
        """Get the parent directory."""
        from nu import FuncCallOp

        return PathI(FuncCallOp(getattr, self, "parent"))

    def root(self) -> StrI:
        """Get the root (e.g., '/' on Unix)."""
        from nu import FuncCallOp, StrI

        return StrI(FuncCallOp(getattr, self, "root"))

    def anchor(self) -> StrI:
        """Get the anchor (drive + root)."""
        from nu import FuncCallOp, StrI

        return StrI(FuncCallOp(getattr, self, "anchor"))

    def parts(self) -> TupleI:
        """Get path parts as a tuple."""
        from nu import FuncCallOp, TupleI

        return TupleI(FuncCallOp(getattr, self, "parts"))

    def parents(self) -> TupleI:
        """Get an immutable sequence of parent paths."""
        from nu import FuncCallOp, TupleI

        return TupleI(FuncCallOp(tuple, FuncCallOp(getattr, self, "parents")))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | str | Nu[str]) -> PathI:
        """Join paths using / operator."""
        from nu import DivOp

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return PathI(DivOp(self, other))

    def joinpath(self, *others: PathArg | str) -> PathI:
        """Join with multiple path components."""
        from nu import MethodCallOp

        wrapped = tuple(PathI(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathI(MethodCallOp(self, "joinpath", *wrapped))

    def with_name(self, name: str | Nu[str]) -> PathI:
        """Return a new path with the name changed."""
        from nu import MethodCallOp

        return PathI(MethodCallOp(self, "with_name", name))

    def with_stem(self, stem: str | Nu[str]) -> PathI:
        """Return a new path with the stem changed."""
        from nu import MethodCallOp

        return PathI(MethodCallOp(self, "with_stem", stem))

    def with_suffix(self, suffix: str | Nu[str]) -> PathI:
        """Return a new path with the suffix changed."""
        from nu import MethodCallOp

        return PathI(MethodCallOp(self, "with_suffix", suffix))

    def resolve_path(self, strict: bool | Nu[bool] = False) -> PathI:
        """Make the path absolute, resolving symlinks.

        Named resolve_path() to avoid collision with RefBase.resolve().
        """
        from nu import MethodCallOp

        return PathI(MethodCallOp(self, "resolve", strict))

    def absolute(self) -> PathI:
        """Make the path absolute (without resolving symlinks)."""
        from nu import MethodCallOp

        return PathI(MethodCallOp(self, "absolute"))

    def relative_to(self, other: PathArg | str | Nu[str]) -> PathI:
        """Compute relative path from other."""
        from nu import MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return PathI(MethodCallOp(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolI:
        """Check if path is absolute."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | str | Nu[str]) -> BoolI:
        """Check if path is relative to other."""
        from nu import BoolI, MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return BoolI(MethodCallOp(self, "is_relative_to", other))

    def match(self, pattern: str | Nu[str]) -> BoolI:
        """Match path against a glob pattern."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolI:
        """Check if path exists."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "exists"))

    def is_file(self) -> BoolI:
        """Check if path is a file."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "is_file"))

    def is_dir(self) -> BoolI:
        """Check if path is a directory."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "is_dir"))

    def is_symlink(self) -> BoolI:
        """Check if path is a symlink."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "is_symlink"))

    def is_mount(self) -> BoolI:
        """Check if path is a mount point."""
        from nu import BoolI, MethodCallOp

        return BoolI(MethodCallOp(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrI:
        """Return path with forward slashes."""
        from nu import MethodCallOp, StrI

        return StrI(MethodCallOp(self, "as_posix"))

    def as_uri(self) -> StrI:
        """Return path as file:// URI."""
        from nu import MethodCallOp, StrI

        return StrI(MethodCallOp(self, "as_uri"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: PathArg) -> BoolI:
        from nu import BoolI, GtOp

        return BoolI(GtOp(self, other))

    def __lt__(self, other: PathArg) -> BoolI:
        from nu import BoolI, LtOp

        return BoolI(LtOp(self, other))

    def __ge__(self, other: PathArg) -> BoolI:
        from nu import BoolI, GeOp

        return BoolI(GeOp(self, other))

    def __le__(self, other: PathArg) -> BoolI:
        from nu import BoolI, LeOp

        return BoolI(LeOp(self, other))

    def eq(self, other: PathArg) -> BoolI:
        from nu import BoolI, EqOp

        return BoolI(EqOp(self, other))

    def ne(self, other: PathArg) -> BoolI:
        from nu import BoolI, NeOp

        return BoolI(NeOp(self, other))


# =============================================================================
# LEAF
# =============================================================================


class PathI(_PathI, TypedNu[Path]):
    """Path leaf - _PathI + TypedNu[Path]."""

    pass
