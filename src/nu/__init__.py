# ruff: noqa
"""Nu: assemble software, don't write it.

Two ways to import. Grab what you need flat from the root:

    from nu import Int, Sequential, Retry, AttrRef, Nu, run

Or reach a subpackage by dot-access:

    import nu
    nu.forms.Int    nu.core.Add    nu.flows.Sequential
    nu.spans.Retry      nu.shape.Shape      nu.tree.map_nodes
    nu.mem.IntRef       nu.virtuals.presets.memory_storage
    nu.ui.Page          nu.std.uuid.UUID

Short aliases: ``nu.m`` = ``nu.mem``, ``nu.nd`` = ``nu.ui``, ``nu.v`` =
``nu.virtuals``. Same modules, shorter to type. ``nu.nd`` still says "nudle"
because nudle is the standard web fabric; the module just lives at ``nu.ui``.

Flat at the root: forms, core interactions, flows, spans, the context fabric,
and the language essentials (``Nu``, the kinds, the ``Arg`` aliases, the
sentinels, the entry points). The shape DSL (``Shape`` / ``Slot``) is flat; its
fabric atoms stay at ``nu.shape.*``. The generic tree toolkit (``nu.tree``) and
the layer-0 engine (``nu.engine``) are namespace-only, never flat.
"""

from __future__ import annotations

# Subpackage namespaces for dot-access.
# Early group: pure layers with no dependency on the flat root surface.
from . import context, core, engine, factory, flows, forms, lang, spans, tree
from .domains import shape

# Flat re-exports: the program-authoring surface.
from .context import *
from .core import *
from .flows import *
from .forms import *
from .spans import *

# Shape DSL only; fabric atoms (Load, SetCmd, ...) stay at nu.shape.*.
from .domains.shape import Shape, Slot

# Language essentials (curated; internals stay at nu.lang.*).
from .lang import (
    EMPTY,
    INVALID,
    Action,
    Arg,
    Attr,
    BoolArg,
    Bracket,
    BytesArg,
    Cardinality,
    Command,
    Context,
    Control,
    DictArg,
    Effect,
    EffectSet,
    Empty,
    ExecOrder,
    FloatArg,
    Flow,
    Form,
    FrozenSetArg,
    IntArg,
    Interaction,
    Invalid,
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
    Sentinel,
    SetArg,
    Sort,
    Span,
    StrArg,
    Strategy,
    StreamAction,
    StreamQuery,
    TupleArg,
    TypedNu,
    compile,
    is_empty,
    is_invalid,
    is_sentinel,
    validate,
)

# Atom builders (nu.factory subpackage): factories, method dispatch, @host.
from .factory import (
    InteractionFactory,
    MethodFactory,
    ScalarQueryFactory,
    host,
    method_action,
    method_command,
    method_query,
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
# the flat root surface (e.g. ``from nu import Shape``). Imported last so their
# init sees a fully-populated ``nu`` module.
from . import invisibles, mem, ray, std, ui, virtuals

# Short aliases for the fabric adapters and UI layer.
m = mem
nd = ui
v = virtuals


# __all__ is everything bound above: the subpackage namespaces, the flat
# re-exports, the shape DSL, and the curated lang + entry-point names. The
# imports are the single source of truth; we just drop privates, the
# __future__ shim, and the internal ``domains`` layer (reached as ``nu.shape``).
# A namespace holds each name once, so dupes can't happen.
_HIDDEN = {"annotations", "domains"}
__all__ = sorted(n for n in dir() if not n.startswith("_") and n not in _HIDDEN)
