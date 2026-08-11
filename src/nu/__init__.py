# ruff: noqa
"""Nu: the interaction primitive.

Build apps in one primitive that spans your whole stack (databases, UIs,
AI agents, and services). No glue. 50x less code.

Two ways to import. Grab what you need flat from the root:

    from nu import Int, Sequential, Retry, AttrRef, Nu, run

Or reach a subpackage by dot-access:

    import nu
    nu.forms.Int    nu.core.Add    nu.flows.Sequential
    nu.spans.Retry      nu.shape.Shape      nu.tree.map_nodes
    nu.mem.IntRef       nu.virtuals.presets.memory_storage
    nu.ui.Page          nu.std.uuid.UUID

Short alias: ``nu.kv`` = ``nu.virtuals`` (the KV-storage fabric).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _version
from typing import TYPE_CHECKING

try:
    __version__ = _version("nustack-py")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
del _version, PackageNotFoundError

from ._config import bootstrap as _bootstrap

_bootstrap()
del _bootstrap

# Subpackage namespaces for dot-access.
# Early group: pure layers with no dependency on the flat root surface.
from . import context, core, engine, factory, flows, forms, lang, spans, tree
from .domains import service, shape

# Flat re-exports: the program-authoring surface.
from .context import *
from .core import *
from .flows import *
from .forms import *
from .spans import *

# Shape DSL only; fabric atoms (Load, SetCmd, ...) stay at nu.shape.*.
from .domains.shape import Shape, Slot
from .domains.service import Method, Service

# Language essentials, curated to the building blocks of a Nu program:
#   - the root kind (``Nu``, ``TypedNu``);
#   - the kind hierarchy (``Ref``, ``Interaction``, ``Query`` / ``ScalarQuery``
#     / ``StreamQuery`` / ``Reduction``, ``Command``, ``Action`` /
#     ``ScalarAction`` / ``StreamAction``, ``Flow`` / ``Strategy`` /
#     ``Control``, ``Span`` / ``Bracket`` / ``Policy``);
#   - the argument aliases used in kind signatures (``Arg`` and the typed
#     ``*Arg`` aliases).
from .lang import (
    Action,
    Arg,
    BoolArg,
    Bracket,
    BytesArg,
    Command,
    Context,
    Control,
    DictArg,
    FloatArg,
    Flow,
    Form,
    FrozenSetArg,
    IntArg,
    Interaction,
    ListArg,
    NoneArg,
    Nu,
    Policy,
    Query,
    Reduction,
    Ref,
    Runtime,
    ScalarAction,
    ScalarQuery,
    SetArg,
    Span,
    StrArg,
    Strategy,
    StreamAction,
    StreamQuery,
    TupleArg,
    TypedNu,
)

# Atom builders (nu.factory subpackage): factories + @host.
from .factory import (
    InteractionFactory,
    ScalarQueryFactory,
    host,
)

# Entry points.
from .lang.helpers import (
    acollect,
    aeval,
    afirst,
    alast,
    arun,
    collect,
    eval,
    eval_in_loop,
    first,
    run,
    run_in_loop,
)

# Late subpackage namespaces: fabric adapters and higher layers that reach into
# the flat root surface (e.g. ``from nu import Shape``). These are heavy and
# transitively pull large trees (storage backends, UI runtime, RPC, ...), so
# they load lazily on first attribute access via ``__getattr__`` below. The
# ``TYPE_CHECKING`` block gives IDEs and type-checkers the real modules so
# ``nu.mem.IntRef`` etc. resolve statically with full completion / go-to-def.
if TYPE_CHECKING:
    from . import http, invisibles, mem, ray, std, ui, virtuals

    # Short alias for the KV storage fabric.
    kv = virtuals

# NOTE: several flat re-exports above shadow Python builtins at module scope
# — coercion atoms (``set``/``frozenset``/``tuple``/``list``/``dict``/``int``/
# ``float``/``str``/``bool``), IO atoms (``print``/``input``), and language
# helpers (``compile``/``eval``). They stay reachable as ``nu.set`` etc., but
# ``from nu import *`` skips them (see ``_SHADOWS_BUILTIN`` below) so callers
# don't get their builtins silently swapped. Any set/dict-builder logic in
# THIS file must use literals (``{...}``) — never the shadowed callables.
_LAZY = {"http", "invisibles", "mem", "ray", "std", "ui", "virtuals"}
_LAZY_ALIASES = {"kv": "virtuals"}


def __getattr__(name):
    import importlib

    if name in _LAZY_ALIASES:
        target = _LAZY_ALIASES[name]
    elif name in _LAZY:
        target = name
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(f".{target}", __name__)
    globals()[name] = mod
    return mod


def __dir__():
    return sorted({*globals(), *_LAZY, *_LAZY_ALIASES})


# __all__ = every name bound above (minus privates, the ``__future__`` shim,
# the internal ``domains`` layer, and any name shadowing a Python builtin)
# plus the lazy fabric + alias names, so ``from nu import *`` and IDE
# discovery see them without forcing import. Builtin-shadowing names stay
# reachable as ``nu.<name>`` — the module dict is unchanged, only ``__all__``
# is filtered — so ``import *`` cannot silently rebind ``set``/``print``/etc.
# in the caller's namespace.
import builtins as _builtins  # noqa: E402  (placed here to avoid the shadowed scope above)

_HIDDEN = {"annotations", "TYPE_CHECKING", "domains"}
_SHADOWS_BUILTIN = {n for n in dir(_builtins) if not n.startswith("_")}
_names = dir()
__all__ = sorted(
    ({*_names, *_LAZY, *_LAZY_ALIASES} - _HIDDEN - _SHADOWS_BUILTIN)
    - {n for n in _names if n.startswith("_")}
)
del _builtins, _names
