"""Path interface - typed wrapper for pathlib.Path.

_PathI provides path operations (constructors, components, manipulation, tests, conversions, comparison).
PathI is the leaf: _PathI + TypedNu[Path].
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Form, Mode, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.forms.collections import ListForm, TupleForm
    from nu.forms.primitives import BoolForm, StrForm


__all__ = ["PathArg", "PathI"]


type PathArg = Arg[Path | PurePath | str]


class _PathI(Form):
    """Path operations mixin - constructors, components, manipulation, tests, conversions, comparison."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> PathI:
        """Create a PathI from a string."""
        from nu import FuncCall

        return PathI(FuncCall(Path, value))

    @classmethod
    def cwd(cls) -> PathI:
        """Get current working directory."""
        from nu import FuncCall

        return PathI(FuncCall(Path.cwd))

    @classmethod
    def home(cls) -> PathI:
        """Get user home directory."""
        from nu import FuncCall

        return PathI(FuncCall(Path.home))

    # =========================================================================
    # PATH COMPONENTS
    # =========================================================================

    def name(self) -> StrForm:
        """Get the final component (filename)."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "name"))

    def stem(self) -> StrForm:
        """Get the filename without the final extension."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "stem"))

    def suffix(self) -> StrForm:
        """Get the file extension (including dot)."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "suffix"))

    def suffixes(self) -> ListForm:
        """Get all file extensions."""
        from nu import FuncCall, ListForm

        return ListForm(FuncCall(getattr, self, "suffixes"))

    def parent(self) -> PathI:
        """Get the parent directory."""
        from nu import FuncCall

        return PathI(FuncCall(getattr, self, "parent"))

    def root(self) -> StrForm:
        """Get the root (e.g., '/' on Unix)."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "root"))

    def anchor(self) -> StrForm:
        """Get the anchor (drive + root)."""
        from nu import FuncCall, StrForm

        return StrForm(FuncCall(getattr, self, "anchor"))

    def parts(self) -> TupleForm:
        """Get path parts as a tuple."""
        from nu import FuncCall, TupleForm

        return TupleForm(FuncCall(getattr, self, "parts"))

    def parents(self) -> TupleForm:
        """Get an immutable sequence of parent paths."""
        from nu import FuncCall, TupleForm

        return TupleForm(FuncCall(tuple, FuncCall(getattr, self, "parents")))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def __truediv__(self, other: PathArg | str | Nu[str]) -> PathI:
        """Join paths using / operator."""
        from nu import Div

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return PathI(Div(self, other))

    def joinpath(self, *others: PathArg | str) -> PathI:
        """Join with multiple path components."""
        from nu import MethodCall

        wrapped = tuple(PathI(o) if isinstance(o, (Path, PurePath)) else o for o in others)
        return PathI(MethodCall(self, "joinpath", *wrapped))

    def with_name(self, name: str | Nu[str]) -> PathI:
        """Return a new path with the name changed."""
        from nu import MethodCall

        return PathI(MethodCall(self, "with_name", name))

    def with_stem(self, stem: str | Nu[str]) -> PathI:
        """Return a new path with the stem changed."""
        from nu import MethodCall

        return PathI(MethodCall(self, "with_stem", stem))

    def with_suffix(self, suffix: str | Nu[str]) -> PathI:
        """Return a new path with the suffix changed."""
        from nu import MethodCall

        return PathI(MethodCall(self, "with_suffix", suffix))

    def resolve_path(self, strict: bool | Nu[bool] = False) -> PathI:
        """Make the path absolute, resolving symlinks.

        Named resolve_path() to avoid collision with RefBase.aresolve().
        """
        from nu import MethodCall

        return PathI(MethodCall(self, "resolve", strict))

    def absolute(self) -> PathI:
        """Make the path absolute (without resolving symlinks)."""
        from nu import MethodCall

        return PathI(MethodCall(self, "absolute"))

    def relative_to(self, other: PathArg | str | Nu[str]) -> PathI:
        """Compute relative path from other."""
        from nu import MethodCall

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return PathI(MethodCall(self, "relative_to", other))

    # =========================================================================
    # PATH TESTS
    # =========================================================================

    def is_absolute(self) -> BoolForm:
        """Check if path is absolute."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "is_absolute"))

    def is_relative_to(self, other: PathArg | str | Nu[str]) -> BoolForm:
        """Check if path is relative to other."""
        from nu import BoolForm, MethodCall

        if isinstance(other, (Path, PurePath)):
            other = PathI(other)
        return BoolForm(MethodCall(self, "is_relative_to", other))

    def match(self, pattern: str | Nu[str]) -> BoolForm:
        """Match path against a glob pattern."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "match", pattern))

    # =========================================================================
    # FILESYSTEM OPERATIONS (executed at runtime)
    # =========================================================================

    def exists(self) -> BoolForm:
        """Check if path exists."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "exists"))

    def is_file(self) -> BoolForm:
        """Check if path is a file."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "is_file"))

    def is_dir(self) -> BoolForm:
        """Check if path is a directory."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "is_dir"))

    def is_symlink(self) -> BoolForm:
        """Check if path is a symlink."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "is_symlink"))

    def is_mount(self) -> BoolForm:
        """Check if path is a mount point."""
        from nu import BoolForm, MethodCall

        return BoolForm(MethodCall(self, "is_mount"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def as_posix(self) -> StrForm:
        """Return path with forward slashes."""
        from nu import MethodCall, StrForm

        return StrForm(MethodCall(self, "as_posix"))

    def as_uri(self) -> StrForm:
        """Return path as file:// URI."""
        from nu import MethodCall, StrForm

        return StrForm(MethodCall(self, "as_uri"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Gt

        return BoolForm(Gt(self, other))

    def __lt__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Lt

        return BoolForm(Lt(self, other))

    def __ge__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Ge

        return BoolForm(Ge(self, other))

    def __le__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Le

        return BoolForm(Le(self, other))

    def eq(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Eq

        return BoolForm(Eq(self, other))

    def ne(self, other: PathArg) -> BoolForm:
        from nu import BoolForm, Ne

        return BoolForm(Ne(self, other))


# =============================================================================
# LEAF
# =============================================================================


class PathI(_PathI, TypedNu[Path]):
    """Path leaf - _PathI + TypedNu[Path]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
