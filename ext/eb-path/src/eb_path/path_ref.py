"""Path type for filesystem paths.

Pattern:
    PathType = Object[Path] + ComparableBase + path operations
    PathValue = ValueBase + PathType (computed results)
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from everybase import Sentinel
from everybase.abc import (
    BoolValue,
    ComparableBase,
    ListValue,
    Object,
    StrValue,
    TupleValue,
    ValueBase,
)


if TYPE_CHECKING:
    from everybase import Term

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
    def from_str(cls, value: str | Term[str]) -> PathValue:
        """Create a PathValue from a string."""
        from everybase.abc import FuncCallOp

        return PathValue(FuncCallOp(Path, value))

    @classmethod
    def cwd(cls) -> PathValue:
        """Get current working directory."""
        from everybase.abc import FuncCallOp

        return PathValue(FuncCallOp(Path.cwd))

    @classmethod
    def home(cls) -> PathValue:
        """Get user home directory."""
        from everybase.abc import FuncCallOp

        return PathValue(FuncCallOp(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrValue:
        """Get the final component (filename)."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "name"))

    def stem(self) -> StrValue:
        """Get the filename without the final extension."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "stem"))

    def suffix(self) -> StrValue:
        """Get the file extension (including dot)."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "suffix"))

    def suffixes(self) -> ListValue:
        """Get all file extensions."""
        from everybase.abc import FuncCallOp

        return ListValue(FuncCallOp(getattr, self, "suffixes"))

    def parent(self) -> PathValue:
        """Get the parent directory."""
        from everybase.abc import FuncCallOp

        return PathValue(FuncCallOp(getattr, self, "parent"))

    def root(self) -> StrValue:
        """Get the root (e.g., '/' on Unix)."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "root"))

    def anchor(self) -> StrValue:
        """Get the anchor (drive + root)."""
        from everybase.abc import FuncCallOp

        return StrValue(FuncCallOp(getattr, self, "anchor"))

    def parts(self) -> TupleValue:
        """Get path parts as a tuple."""
        from everybase.abc import FuncCallOp

        return TupleValue(FuncCallOp(getattr, self, "parts"))

    def parents(self) -> TupleValue:
        """Get an immutable sequence of parent paths."""
        from everybase.abc import FuncCallOp

        return TupleValue(FuncCallOp(tuple, FuncCallOp(getattr, self, "parents")))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | str | Term[str]) -> PathValue:
        """Join paths using / operator."""
        from everybase.abc import DivOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return PathValue(DivOp(self, other))

    def joinpath(self, *others: PathArg | str) -> PathValue:
        """Join with multiple path components."""
        from everybase.abc import MethodCallOp

        wrapped = tuple(PathValue(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathValue(MethodCallOp(self, "joinpath", *wrapped))

    def with_name(self, name: str | Term[str]) -> PathValue:
        """Return a new path with the name changed."""
        from everybase.abc import MethodCallOp

        return PathValue(MethodCallOp(self, "with_name", name))

    def with_stem(self, stem: str | Term[str]) -> PathValue:
        """Return a new path with the stem changed."""
        from everybase.abc import MethodCallOp

        return PathValue(MethodCallOp(self, "with_stem", stem))

    def with_suffix(self, suffix: str | Term[str]) -> PathValue:
        """Return a new path with the suffix changed."""
        from everybase.abc import MethodCallOp

        return PathValue(MethodCallOp(self, "with_suffix", suffix))

    def resolve_path(self, strict: bool | Term[bool] = False) -> PathValue:
        """Make the path absolute, resolving symlinks.

        Named resolve_path() to avoid collision with RefBase.resolve().
        """
        from everybase.abc import MethodCallOp

        return PathValue(MethodCallOp(self, "resolve", strict))

    def absolute(self) -> PathValue:
        """Make the path absolute (without resolving symlinks)."""
        from everybase.abc import MethodCallOp

        return PathValue(MethodCallOp(self, "absolute"))

    def relative_to(self, other: PathArg | str | Term[str]) -> PathValue:
        """Compute relative path from other."""
        from everybase.abc import MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return PathValue(MethodCallOp(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolValue:
        """Check if path is absolute."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | str | Term[str]) -> BoolValue:
        """Check if path is relative to other."""
        from everybase.abc import MethodCallOp

        if isinstance(other, (Path, PurePath)):
            other = PathValue(other)
        return BoolValue(MethodCallOp(self, "is_relative_to", other))

    def match(self, pattern: str | Term[str]) -> BoolValue:
        """Match path against a glob pattern."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolValue:
        """Check if path exists."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "exists"))

    def is_file(self) -> BoolValue:
        """Check if path is a file."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_file"))

    def is_dir(self) -> BoolValue:
        """Check if path is a directory."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_dir"))

    def is_symlink(self) -> BoolValue:
        """Check if path is a symlink."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_symlink"))

    def is_mount(self) -> BoolValue:
        """Check if path is a mount point."""
        from everybase.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrValue:
        """Return path with forward slashes."""
        from everybase.abc import MethodCallOp

        return StrValue(MethodCallOp(self, "as_posix"))

    def as_uri(self) -> StrValue:
        """Return path as file:// URI."""
        from everybase.abc import MethodCallOp

        return StrValue(MethodCallOp(self, "as_uri"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class PathValue(ValueBase, PathType):
    """Computed Path value (Python memory substrate)."""

    pass
