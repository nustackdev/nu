"""``pathlib.PurePath`` as a Form: ``Path`` - pure path operations only.

The name is ``Path`` to mirror ``from pathlib import Path``, but it is backed by
``PurePath`` (``from pathlib import PurePath as _PurePath``) so it models the
*pure* surface - the lexical path operations that never touch the filesystem.
Filesystem I/O (``exists``, ``read_text``, ``iterdir`` ...) is deferred.

The operations split the two ways the model intends:

- **property reads** (``.name``, ``.suffix``, ``.parent`` ...) reuse core
  ``GetAttr`` - a path component is just an attribute read.
- **method calls** (``with_suffix``, ``joinpath``, ``as_posix`` ...) are named
  ``ScalarQueryFactory`` atoms in ``interactions`` (each binds the unbound
  ``PurePath`` method).
- **the ``/`` operator** is sugar for ``joinpath``.
- **comparison** reuses the core comparison atoms (``PurePath`` is orderable and
  equatable).
- **constructors** are ``ScalarQueryFactory`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.

Deferred (filesystem I/O, same template when added): ``exists``, ``is_file``,
``is_dir``, ``resolve``, ``absolute``, ``read_text``, ``iterdir``, ``glob``,
plus the pure ``is_reserved`` / ``parents`` sequence.
"""

from __future__ import annotations

from pathlib import PurePath as _PurePath
from typing import TYPE_CHECKING, TypeAlias

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.collections import List, Tuple
    from nu.forms.primitives import Bool, Str
    from nu.lang import Arg, StrArg

    PathArg: TypeAlias = "Arg[_PurePath]"


__all__ = ["Path"]


class Path(Form, TypedNu[_PurePath]):
    """``pathlib`` path as a Form - the pure (no filesystem I/O) surface.

    Named ``Path`` to mirror ``from pathlib import Path``; backed by
    ``PurePath``, so only the lexical operations are modeled. Build one with
    ``Path.of(...)``; read its components as properties; transform it with the
    method calls or the ``/`` operator.
    """

    # =========================================================================
    # CONSTRUCTORS (new atoms in interactions)
    # =========================================================================

    @classmethod
    def of(cls, *segments: StrArg | PathArg) -> Path:
        """Build a path from segments: ``PurePath(*segments)``."""
        from .interactions import PathOf

        return Path(PathOf(*segments))

    @classmethod
    def cwd(cls) -> Path:
        """The current working directory: ``Path.cwd()``."""
        from .interactions import PathCwd

        return Path(PathCwd())

    @classmethod
    def home(cls) -> Path:
        """The user's home directory: ``Path.home()``."""
        from .interactions import PathHome

        return Path(PathHome())

    # =========================================================================
    # COMPONENT READS (reuse core GetAttr)
    # =========================================================================

    def name(self) -> Str:
        """The final component (filename)."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "name"))

    def stem(self) -> Str:
        """The final component without its suffix."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "stem"))

    def suffix(self) -> Str:
        """The file extension of the final component (including the dot)."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "suffix"))

    def suffixes(self) -> List:
        """All file extensions of the final component."""
        from nu.core import GetAttr
        from nu.forms import List

        return List(GetAttr(self, "suffixes"))

    def parts(self) -> Tuple:
        """The path's components as a tuple."""
        from nu.core import GetAttr
        from nu.forms import Tuple

        return Tuple(GetAttr(self, "parts"))

    def parent(self) -> Path:
        """The logical parent of the path."""
        from nu.core import GetAttr

        return Path(GetAttr(self, "parent"))

    def root(self) -> Str:
        """The root (e.g. ``/`` on POSIX)."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "root"))

    def anchor(self) -> Str:
        """The concatenation of drive and root."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "anchor"))

    def drive(self) -> Str:
        """The drive (empty on POSIX)."""
        from nu.core import GetAttr
        from nu.forms import Str

        return Str(GetAttr(self, "drive"))

    # =========================================================================
    # PATH-RETURNING METHODS (factory atoms over unbound methods)
    # =========================================================================

    def with_name(self, name: StrArg) -> Path:
        """A copy with the final component's name replaced."""
        from .interactions import PathWithName

        return Path(PathWithName(self, name))

    def with_stem(self, stem: StrArg) -> Path:
        """A copy with the final component's stem replaced."""
        from .interactions import PathWithStem

        return Path(PathWithStem(self, stem))

    def with_suffix(self, suffix: StrArg) -> Path:
        """A copy with the final component's suffix replaced."""
        from .interactions import PathWithSuffix

        return Path(PathWithSuffix(self, suffix))

    def joinpath(self, *others: StrArg | PathArg) -> Path:
        """Join one or more components onto the path."""
        from .interactions import PathJoinpath

        return Path(PathJoinpath(self, *others))

    def relative_to(self, other: StrArg | PathArg) -> Path:
        """The path relative to ``other``."""
        from .interactions import PathRelativeTo

        return Path(PathRelativeTo(self, other))

    def __truediv__(self, other: StrArg | PathArg) -> Path:
        """Join with ``/``: ``Path.of("a") / "b"``."""
        from .interactions import PathJoinpath

        return Path(PathJoinpath(self, other))

    # =========================================================================
    # STRING CONVERSIONS (factory atoms)
    # =========================================================================

    def as_posix(self) -> Str:
        """The path as a string with forward slashes."""
        from nu.forms import Str

        from .interactions import PathAsPosix

        return Str(PathAsPosix(self))

    def as_uri(self) -> Str:
        """The path as a ``file://`` URI (requires an absolute path)."""
        from nu.forms import Str

        from .interactions import PathAsUri

        return Str(PathAsUri(self))

    # =========================================================================
    # PREDICATES (factory atoms)
    # =========================================================================

    def match(self, pattern: StrArg) -> Bool:
        """Whether the path matches a glob pattern."""
        from nu.forms import Bool

        from .interactions import PathMatch

        return Bool(PathMatch(self, pattern))

    def is_absolute(self) -> Bool:
        """Whether the path is absolute."""
        from nu.forms import Bool

        from .interactions import PathIsAbsolute

        return Bool(PathIsAbsolute(self))

    def is_relative_to(self, other: StrArg | PathArg) -> Bool:
        """Whether the path is relative to ``other``."""
        from nu.forms import Bool

        from .interactions import PathIsRelativeTo

        return Bool(PathIsRelativeTo(self, other))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: PathArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: PathArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: PathArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: PathArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: PathArg) -> Bool:
        """Whether two paths are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: PathArg) -> Bool:
        """Whether two paths differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
