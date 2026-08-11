"""pathlib interactions - one ``host`` binding per host call.

Constructors bind the class / its classmethods; methods bind the *unbound*
method (a plain callable whose first argument is the receiver, so
``p.with_suffix(s)`` is ``PurePath.with_suffix(p, s)``). Property reads
(``.name``, ``.suffix``, ``.parent`` ...) are not here - they reuse core
``GetAttr`` from the Form. Comparison reuses the core atoms.

Everything is backed by ``PurePath`` - the pure (no filesystem I/O) half of
``pathlib``. ``cwd`` / ``home`` are the two exceptions: they read the process
environment, so they bind the concrete ``Path`` classmethods and declare
``deterministic=False`` to stay un-folded.
"""

from __future__ import annotations

from pathlib import Path as _Path
from pathlib import PurePath as _PurePath

from nu.factory import host


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

PathOf = host(_PurePath, name="PathOf")
PathCwd = host(_Path.cwd, name="PathCwd", deterministic=False)
PathHome = host(_Path.home, name="PathHome", deterministic=False)

# --- path-returning methods -------------------------------------------------

PathWithName = host(_PurePath.with_name, name="PathWithName")
PathWithStem = host(_PurePath.with_stem, name="PathWithStem")
PathWithSuffix = host(_PurePath.with_suffix, name="PathWithSuffix")
PathJoinpath = host(_PurePath.joinpath, name="PathJoinpath")
PathRelativeTo = host(_PurePath.relative_to, name="PathRelativeTo")

# --- string conversions -----------------------------------------------------

PathAsPosix = host(_PurePath.as_posix, name="PathAsPosix")
PathAsUri = host(_PurePath.as_uri, name="PathAsUri")

# --- predicate methods ------------------------------------------------------

PathMatch = host(_PurePath.match, name="PathMatch")
PathIsAbsolute = host(_PurePath.is_absolute, name="PathIsAbsolute")
PathIsRelativeTo = host(_PurePath.is_relative_to, name="PathIsRelativeTo")
