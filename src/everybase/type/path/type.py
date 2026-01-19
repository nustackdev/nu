"""Path Type."""

from __future__ import annotations

from pathlib import Path, PurePath  # noqa: F401

from everyterm.ops import DivOp, FuncCallOp, MethodCallOp
from everyterm.term import BoolArg, StrArg
from everyterm.types import BaseType, BoolType, ComparisonBase, ListType, StrType, TupleType
from everyterm.typing import Sentinel

from .args import PathArg


__all__ = [
    "PathType",
]


class PathType(
    ComparisonBase["Path | PurePath | str | PathType"],
    BaseType[Path | PurePath | Sentinel],
):
    """Type representing a filesystem path.

    Provides path manipulation operations. Stored as string.

    Example:
        >>> p = PathType.from_str("/home/user/data.txt")
        >>> p.parent()      # PathType
        >>> p.name()        # StrType
        >>> p.exists()      # BoolType (at execution time)
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: StrArg) -> PathType:
        """Create a PathType from a string."""
        return cls(FuncCallOp(Path, value))

    @classmethod
    def cwd(cls) -> PathType:
        """Get current working directory."""
        return cls(FuncCallOp(Path.cwd))

    @classmethod
    def home(cls) -> PathType:
        """Get user home directory."""
        return cls(FuncCallOp(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrType:
        """Get the final component (filename)."""
        return StrType(FuncCallOp(getattr, self, "name"))

    def stem(self) -> StrType:
        """Get the filename without the final extension."""
        return StrType(FuncCallOp(getattr, self, "stem"))

    def suffix(self) -> StrType:
        """Get the file extension (including dot)."""
        return StrType(FuncCallOp(getattr, self, "suffix"))

    def suffixes(self) -> ListType:
        """Get all file extensions."""
        return ListType(FuncCallOp(getattr, self, "suffixes"))

    def parent(self) -> PathType:
        """Get the parent directory."""
        return PathType(FuncCallOp(getattr, self, "parent"))

    def parents(self) -> TupleType:
        """Get sequence of parent directories."""
        return TupleType(FuncCallOp(getattr, self, "parents"))

    def root(self) -> StrType:
        """Get the root (e.g., '/' on Unix)."""
        return StrType(FuncCallOp(getattr, self, "root"))

    def anchor(self) -> StrType:
        """Get the anchor (drive + root)."""
        return StrType(FuncCallOp(getattr, self, "anchor"))

    def parts(self) -> TupleType:
        """Get path components as tuple."""
        return TupleType(FuncCallOp(getattr, self, "parts"))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | StrArg) -> PathType:
        """Join paths using / operator."""
        if isinstance(other, (Path, PurePath)):
            other = PathType(other)
        return PathType(DivOp(self, other))

    def joinpath(self, *others: PathArg | StrArg) -> PathType:
        """Join with multiple path components."""
        wrapped = tuple(PathType(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathType(MethodCallOp(self, "joinpath", *wrapped))

    def with_name(self, name: StrArg) -> PathType:
        """Return a new path with the name changed."""
        return PathType(MethodCallOp(self, "with_name", name))

    def with_stem(self, stem: StrArg) -> PathType:
        """Return a new path with the stem changed."""
        return PathType(MethodCallOp(self, "with_stem", stem))

    def with_suffix(self, suffix: StrArg) -> PathType:
        """Return a new path with the suffix changed."""
        return PathType(MethodCallOp(self, "with_suffix", suffix))

    def resolve(self, strict: BoolArg = False) -> PathType:
        """Make the path absolute."""
        return PathType(MethodCallOp(self, "resolve", strict))

    def absolute(self) -> PathType:
        """Make the path absolute (without resolving symlinks)."""
        return PathType(MethodCallOp(self, "absolute"))

    def relative_to(self, other: PathArg | StrArg) -> PathType:
        """Compute relative path from other."""
        if isinstance(other, (Path, PurePath)):
            other = PathType(other)
        return PathType(MethodCallOp(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolType:
        """Check if path is absolute."""
        return BoolType(MethodCallOp(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | StrArg) -> BoolType:
        """Check if path is relative to other."""
        if isinstance(other, (Path, PurePath)):
            other = PathType(other)
        return BoolType(MethodCallOp(self, "is_relative_to", other))

    def match(self, pattern: StrArg) -> BoolType:
        """Match path against a glob pattern."""
        return BoolType(MethodCallOp(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolType:
        """Check if path exists."""
        return BoolType(MethodCallOp(self, "exists"))

    def is_file(self) -> BoolType:
        """Check if path is a file."""
        return BoolType(MethodCallOp(self, "is_file"))

    def is_dir(self) -> BoolType:
        """Check if path is a directory."""
        return BoolType(MethodCallOp(self, "is_dir"))

    def is_symlink(self) -> BoolType:
        """Check if path is a symlink."""
        return BoolType(MethodCallOp(self, "is_symlink"))

    def is_mount(self) -> BoolType:
        """Check if path is a mount point."""
        return BoolType(MethodCallOp(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrType:
        """Return path with forward slashes."""
        return StrType(MethodCallOp(self, "as_posix"))

    def as_uri(self) -> StrType:
        """Return path as file:// URI."""
        return StrType(MethodCallOp(self, "as_uri"))
