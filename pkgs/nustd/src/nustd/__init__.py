# ruff: noqa
"""Batteries for Nu: the fabrics and the standard library.

One import, then dot-access::

    import nustd

    nustd.kv.presets.memory_storage    nustd.mem.IntRef
    nustd.ui.Page                      nustd.service.Method
    nustd.uuid.UUID                    nustd.datetime.Now

Two kinds of thing live here, side by side.

**Fabrics** (``kv``, ``mem``, ``ui``, ``ws_server``, ``service``, ``llm``,
``cc``, ``http``, ``proxy``, ``mp``, ``mp_pool``, ``cluster``) back a Shape
with somewhere real to live: a store, a browser, a process pool, a model. Each
is heavy and pulls a large tree behind it (storage backends, the UI runtime,
RPC, ray), so they load on first attribute access, not on ``import nustd``.

**The standard library** (``uuid``, ``datetime``, ``decimal``, ``math`` ...)
mirrors Python's stdlib module by module. A value type is a **Form** - the
typed access surface you call methods on. Its operations are **interactions**:
reused from ``nu.core`` where they already exist (comparison, attribute reads,
casts) or added alongside the Form as new atoms where core can't express them
(e.g. constructors). No opaque ``FuncCall`` escape hatch - every op is a
first-class term. These are pure and cheap, so they import eagerly.

The kernel is the other package, and it stays independent of this one::

    import nu
    nu.Int, nu.Sequential, nu.Shape, nu.run
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _version
from typing import TYPE_CHECKING


try:
    __version__ = _version("nustd")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
del _version, PackageNotFoundError

# The standard library: pure Nu surfaces over Python's stdlib, cheap to import.
from . import (
    asyncio,
    cmath,
    datetime,
    decimal,
    fin,
    fractions,
    functools,
    itertools,
    logging,
    math,
    pathlib,
    random,
    time,
    uuid,
)

# The fabrics load lazily through ``__getattr__`` below - each one reaches for
# a backend (rocksdb, ray, the UI runtime, an HTTP client) that has no business
# being imported by someone who only wanted ``nustd.uuid``. The
# ``TYPE_CHECKING`` block hands the real modules to IDEs and type-checkers, so
# ``nustd.kv.ShapeStore`` resolves statically with full completion and
# go-to-definition despite never being bound at import time.
if TYPE_CHECKING:
    from . import cc, cluster, http, kv, llm, mem, mp, mp_pool, proxy, service, ui, ws_server

# Value is the extra that pulls the fabric's backend, or None when the fabric
# needs nothing beyond a plain ``nustd`` install.
_LAZY = {
    "cc": "cc",
    "cluster": "cluster",
    "http": "http",
    "kv": "kv",
    "llm": "llm",
    "mem": "mem",
    "mp": None,
    "mp_pool": None,
    "proxy": "proxy",
    "service": None,
    "ui": "ui",
    "ws_server": "ws_server",
}


def __getattr__(name):
    import importlib

    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        mod = importlib.import_module(f".{name}", __name__)
    except ImportError as exc:
        # The fabric ships in this wheel, so a failure here is its backend
        # missing, not the fabric. Point at the extra that supplies it.
        extra = _LAZY[name]
        if extra is None:
            raise
        msg = f"nustd.{name} requires its backend: pip install nustd[{extra}]"
        raise AttributeError(msg) from exc
    globals()[name] = mod
    return mod


def __dir__():
    return sorted({*globals(), *_LAZY})


__all__ = sorted(
    {
        "asyncio",
        "cmath",
        "datetime",
        "decimal",
        "fin",
        "fractions",
        "functools",
        "itertools",
        "logging",
        "math",
        "pathlib",
        "random",
        "time",
        "uuid",
        *_LAZY,
    }
)
