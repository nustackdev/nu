"""nu.mem: the shape fabric over plain nested Python dicts, part of the kernel.

Local state is something every program has, so this fabric ships with the
core rather than in ``nustd``, and its refs and interactions are flat at the
root too.

A Shape declares slots, each slot is a ref, and every ref is a path of keys
into one dict you hand in. No storage backend, no views, no reactivity: reads
walk the dict, writes mutate it in place, and the dict stays yours to print,
copy or dump.

A missing key on the way down reads EMPTY rather than raising, and a write
creates whatever levels it needs, so a Shape can be laid over an empty dict
and filled in as it goes.

Usage::

    import nu

    class User(nu.Shape):
        name = nu.StrRef.slot()
        age = nu.IntRef.slot()

    data = {}
    ctx = nu.Context().bind(dict, data, User)

The core leaves (``IntRef``, ``StrRef``, ``FloatRef``, ``BoolRef``,
``BytesRef``, ``ObjectRef``) each carry their value Form, so the ref itself is
an operand. Leaves for standard-library values live with their library
(``nustd.decimal.mem.DecimalRef``, ``nustd.datetime.mem.DatetimeRef``, ...).
Containers (``ListRef``, ``DictRef``, ``SetRef``) hold a plain list, dict or
set, and descend to the ref for the value they declare: a core leaf for a core
Python type, the leaf class itself when one is passed, a ``ShapeRef`` when the
value is a Shape, and ``ObjectRef`` for anything else. ``ShapeRef`` nests one
Shape inside another. ``ProgramRef`` holds Nu source.

``Frame`` is the stack frame of a Nu program: a fresh dict bound for one
Shape around one body, for the values a body computes once and reads again,
counts or accumulates. ``let`` is the one-value frame: an anonymous slot
holding one disposable value for one body. ``Throttle`` and ``Debounce`` keep
their state in a mem ref the caller passes.

What goes into a Nu constructor is a tree, even a literal, and a mem ref is
no exception: it names where a value will be when the program runs, not the
value. Build-time Python may shape the tree but never branches on or computes
with the values going into it. The function a binder such as ``let`` takes
runs once, at construction, and only builds the tree; decisions over the
value are nodes of that tree.

So never write a Python ``if`` or arithmetic on a value on its way into a
constructor, even one you can see: ``"high" if price > 100 else "low"``
decides once, at build time, for every run. Build the Nu expression,
``nu.If(p > 100, "high", "low")``, and the run decides.
"""

from nu.mem import interactions, refs
from nu.mem.interactions import Debounce, Frame, Throttle, let
from nu.mem.refs import (
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    ObjectRef,
    ProgramRef,
    SetRef,
    ShapeRef,
    StrRef,
)


__all__ = [
    "BoolRef",
    "BytesRef",
    "Debounce",
    "DictRef",
    "FloatRef",
    "Frame",
    "IntRef",
    "ListRef",
    "ObjectRef",
    "ProgramRef",
    "SetRef",
    "ShapeRef",
    "StrRef",
    "Throttle",
    "interactions",
    "let",
    "refs",
]
