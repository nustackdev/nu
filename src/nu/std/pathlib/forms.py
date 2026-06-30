"""``pathlib.PurePath`` as a Form: ``Path`` - pure path operations only.

The name is ``Path`` to mirror ``from pathlib import Path``, but it is backed by
``PurePath`` (``from pathlib import PurePath as _PurePath``) so it models the
*pure* surface - the lexical path operations that never touch the filesystem.
Filesystem I/O (``exists``, ``read_text``, ``iterdir`` ...) is deferred.

The operations split the two ways the model intends:

- **property reads** (``.name``, ``.suffix``, ``.parent`` ...) reuse core
  ``GetAttrQuery`` - a path component is just an attribute read.
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
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.collections import ListForm, TupleForm
    from nu.forms.primitives import BoolForm, StrForm
    from nu.lang import Arg, StrArg

    type PathArg = Arg[_PurePath]


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
    # COMPONENT READS (reuse core GetAttrQuery)
    # =========================================================================

    def name(self) -> StrForm:
        """The final component (filename)."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "name"))

    def stem(self) -> StrForm:
        """The final component without its suffix."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "stem"))

    def suffix(self) -> StrForm:
        """The file extension of the final component (including the dot)."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "suffix"))

    def suffixes(self) -> ListForm:
        """All file extensions of the final component."""
        from nu import ListForm
        from nu.core import GetAttrQuery

        return ListForm(GetAttrQuery(self, "suffixes"))

    def parts(self) -> TupleForm:
        """The path's components as a tuple."""
        from nu import TupleForm
        from nu.core import GetAttrQuery

        return TupleForm(GetAttrQuery(self, "parts"))

    def parent(self) -> Path:
        """The logical parent of the path."""
        from nu.core import GetAttrQuery

        return Path(GetAttrQuery(self, "parent"))

    def root(self) -> StrForm:
        """The root (e.g. ``/`` on POSIX)."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "root"))

    def anchor(self) -> StrForm:
        """The concatenation of drive and root."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "anchor"))

    def drive(self) -> StrForm:
        """The drive (empty on POSIX)."""
        from nu import StrForm
        from nu.core import GetAttrQuery

        return StrForm(GetAttrQuery(self, "drive"))

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

    def as_posix(self) -> StrForm:
        """The path as a string with forward slashes."""
        from nu import StrForm

        from .interactions import PathAsPosix

        return StrForm(PathAsPosix(self))

    def as_uri(self) -> StrForm:
        """The path as a ``file://`` URI (requires an absolute path)."""
        from nu import StrForm

        from .interactions import PathAsUri

        return StrForm(PathAsUri(self))

    # =========================================================================
    # PREDICATES (factory atoms)
    # =========================================================================

    def match(self, pattern: StrArg) -> BoolForm:
        """Whether the path matches a glob pattern."""
        from nu import BoolForm

        from .interactions import PathMatch

        return BoolForm(PathMatch(self, pattern))

    def is_absolute(self) -> BoolForm:
        """Whether the path is absolute."""
        from nu import BoolForm

        from .interactions import PathIsAbsolute

        return BoolForm(PathIsAbsolute(self))

    def is_relative_to(self, other: StrArg | PathArg) -> BoolForm:
        """Whether the path is relative to ``other``."""
        from nu import BoolForm

        from .interactions import PathIsRelativeTo

        return BoolForm(PathIsRelativeTo(self, other))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GtQuery

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LtQuery

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GeQuery

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: PathArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LeQuery

        return BoolForm(LeQuery(self, other))

    def eq(self, other: PathArg) -> BoolForm:
        """Whether two paths are equal."""
        from nu import BoolForm
        from nu.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def ne(self, other: PathArg) -> BoolForm:
        """Whether two paths differ."""
        from nu import BoolForm
        from nu.core import NeQuery

        return BoolForm(NeQuery(self, other))
