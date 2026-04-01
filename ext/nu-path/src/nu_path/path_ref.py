"""Path type for filesystem paths.

Pattern:
    PathType = Object[Path] + ComparableBase + path operations
    PathValue = Interface + PathType (computed results)
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    BoolI,
    ComparableBase,
    ListI,
    Object,
    StrI,
    TupleI,
    Interface,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import PathArg


__all__ = [
    "PathType",
    "PathValue",
]


class PathType(
    ComparableBase["Path | PurePath | str | PathType"],
    Object[Path | Sentinel],
):
    """Abstract type for Path operations.

    Provides path manipulation operations.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> PathValue:
        """Create a PathValue from a string."""
        from nu import FuncCallOp

        return PathValue(FuncCallOp(Path, value))

    @classmethod
    def cwd(cls) -> PathValue:
        """Get current working directory."""
        from nu import FuncCallOp

        return PathValue(FuncCallOp(Path.cwd))

    @classmethod
    def home(cls) -> PathValue:
        """Get user home directory."""
        from nu import FuncCallOp

        return PathValue(FuncCallOp(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrI:
        """Get the final component (filename)."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "name"))

    def stem(self) -> StrI:
        """Get the filename without the final extension."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "stem"))

    def suffix(self) -> StrI:
        """Get the file extension (including dot)."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "suffix"))

    def suffixes(self) -> ListI:
        """Get all file extensions."""
        from nu import FuncCallOp

        return ListI(FuncCallOp(getattr, self, "suffixes"))

    def parent(self) -> PathValue:
        """Get the parent directory."""
        from nu import FuncCallOp

        return PathValue(FuncCallOp(getattr, self, "parent"))

    def root(self) -> StrI:
        """Get the root (e.g., '/' on Unix)."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "root"))

    def anchor(self) -> StrI:
        """Get the anchor (drive + root)."""
        from nu import FuncCallOp

        return StrI(FuncCallOp(getattr, self, "anchor"))

    def parts(self) -> TupleI:
        """Get path parts as a tuple."""
        from nu import FuncCallOp

        return TupleI(FuncCallOp(getattr, self, "parts"))

    def parents(self) -> TupleI:
        """Get an immutable sequence of parent paths."""
        from nu import FuncCallOp

        return TupleI(FuncCallOp(tuple, FuncCallOp(getattr, self, "parents")))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | str | Nu[str]) -> PathValue:
        """Join paths using / operator."""
        from nu import DivOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return PathValue(DivOp(self, other))

    def joinpath(self, *others: PathArg | str) -> PathValue:
        """Join with multiple path components."""
        from nu import MethodCallOp

        wrapped = tuple(PathValue(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathValue(MethodCallOp(self, "joinpath", *wrapped))

    def with_name(self, name: str | Nu[str]) -> PathValue:
        """Return a new path with the name changed."""
        from nu import MethodCallOp

        return PathValue(MethodCallOp(self, "with_name", name))

    def with_stem(self, stem: str | Nu[str]) -> PathValue:
        """Return a new path with the stem changed."""
        from nu import MethodCallOp

        return PathValue(MethodCallOp(self, "with_stem", stem))

    def with_suffix(self, suffix: str | Nu[str]) -> PathValue:
        """Return a new path with the suffix changed."""
        from nu import MethodCallOp

        return PathValue(MethodCallOp(self, "with_suffix", suffix))

    def resolve_path(self, strict: bool | Nu[bool] = False) -> PathValue:
        """Make the path absolute, resolving symlinks.

        Named resolve_path() to avoid collision with RefBase.resolve().
        """
        from nu import MethodCallOp

        return PathValue(MethodCallOp(self, "resolve", strict))

    def absolute(self) -> PathValue:
        """Make the path absolute (without resolving symlinks)."""
        from nu import MethodCallOp

        return PathValue(MethodCallOp(self, "absolute"))

    def relative_to(self, other: PathArg | str | Nu[str]) -> PathValue:
        """Compute relative path from other."""
        from nu import MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return PathValue(MethodCallOp(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolI:
        """Check if path is absolute."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | str | Nu[str]) -> BoolI:
        """Check if path is relative to other."""
        from nu import MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return BoolI(MethodCallOp(self, "is_relative_to", other))

    def match(self, pattern: str | Nu[str]) -> BoolI:
        """Match path against a glob pattern."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolI:
        """Check if path exists."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "exists"))

    def is_file(self) -> BoolI:
        """Check if path is a file."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_file"))

    def is_dir(self) -> BoolI:
        """Check if path is a directory."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_dir"))

    def is_symlink(self) -> BoolI:
        """Check if path is a symlink."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_symlink"))

    def is_mount(self) -> BoolI:
        """Check if path is a mount point."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrI:
        """Return path with forward slashes."""
        from nu import MethodCallOp

        return StrI(MethodCallOp(self, "as_posix"))

    def as_uri(self) -> StrI:
        """Return path as file:// URI."""
        from nu import MethodCallOp

        return StrI(MethodCallOp(self, "as_uri"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class PathValue(Interface, PathType):
    """Computed Path value (Python memory substrate)."""

    pass
