"""pathlib interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind the class / its classmethods; methods bind the *unbound*
method (a plain callable whose first argument is the receiver, so
``p.with_suffix(s)`` is ``PurePath.with_suffix(p, s)``). Property reads
(``.name``, ``.suffix``, ``.parent`` ...) are not here - they reuse core
``GetAttrQuery`` from the Form. Comparison reuses the core atoms.

Everything is backed by ``PurePath`` - the pure (no filesystem I/O) half of
``pathlib``. ``cwd`` / ``home`` are the two exceptions: they read the process
environment, so they bind the concrete ``Path`` classmethods and declare
``deterministic=False`` to stay un-folded.
"""

from __future__ import annotations

from pathlib import Path as _Path
from pathlib import PurePath as _PurePath

from nu.factory import ScalarQueryFactory


__all__ = [
    "PathAsPosix",
    "PathAsUri",
    "PathCwd",
    "PathHome",
    "PathIsAbsolute",
    "PathIsRelativeTo",
    "PathJoinpath",
    "PathMatch",
    "PathOf",
    "PathRelativeTo",
    "PathWithName",
    "PathWithStem",
    "PathWithSuffix",
]


# --- constructors -----------------------------------------------------------

PathOf = ScalarQueryFactory("PathOf", _PurePath)
PathCwd = ScalarQueryFactory("PathCwd", _Path.cwd, deterministic=False)
PathHome = ScalarQueryFactory("PathHome", _Path.home, deterministic=False)

# --- path-returning methods -------------------------------------------------

PathWithName = ScalarQueryFactory("PathWithName", _PurePath.with_name)
PathWithStem = ScalarQueryFactory("PathWithStem", _PurePath.with_stem)
PathWithSuffix = ScalarQueryFactory("PathWithSuffix", _PurePath.with_suffix)
PathJoinpath = ScalarQueryFactory("PathJoinpath", _PurePath.joinpath)
PathRelativeTo = ScalarQueryFactory("PathRelativeTo", _PurePath.relative_to)

# --- string conversions -----------------------------------------------------

PathAsPosix = ScalarQueryFactory("PathAsPosix", _PurePath.as_posix)
PathAsUri = ScalarQueryFactory("PathAsUri", _PurePath.as_uri)

# --- predicate methods ------------------------------------------------------

PathMatch = ScalarQueryFactory("PathMatch", _PurePath.match)
PathIsAbsolute = ScalarQueryFactory("PathIsAbsolute", _PurePath.is_absolute)
PathIsRelativeTo = ScalarQueryFactory("PathIsRelativeTo", _PurePath.is_relative_to)
