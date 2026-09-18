"""MRO walking: a class in, its callable members out, attributed to definers.

For a class `C`, the answer to "what can be called on it" is spread across its
MRO. This walk resolves each name to the class that actually defines it, so a
consumer sees `append` once, tagged with `MutableSequenceForm`, and does not
have to walk the hierarchy itself.

No Nu knowledge. The caller supplies the stop class, and everything at or
above it is left alone. That is how `>>`, `|` and `&` stay the `Nu` record's
business rather than reappearing on every Form and Ref.
"""

from __future__ import annotations

from dataclasses import dataclass


__all__ = [
    "Binding",
    "walk_bindings",
]


@dataclass(frozen=True)
class Binding:
    """One callable member reached from a class, and where it is defined."""

    name: str
    target: object
    defining: type
    raw: object  # the raw descriptor from the defining class's __dict__


def walk_bindings(
    cls: type,
    *,
    stop: type,
    include_dunders: bool = True,
    skip: frozenset[str] = frozenset(),
) -> tuple[Binding, ...]:
    """Every callable member ``cls`` inherits from below ``stop``.

    Walks ``cls.__mro__`` and for each public name, or each dunder we care
    about, finds the first class whose ``__dict__`` defines it. Classes at or
    above ``stop`` are ignored, so anything they carry belongs to their own
    record and not to ``cls``.

    Args:
        cls: the class to walk.
        stop: the horizon; a class at or above ``stop`` in the MRO is skipped.
        include_dunders: whether to include the operator dunders we recognise.
        skip: names to leave out. Used for the declaration-time DSL entries
            (``slot``, ``method``) that belong to the shape and service kinds
            rather than to the form/ref surface.

    Returns:
        One Binding per resolved name, in MRO order (most specific first).
        Members whose raw entry is not callable are dropped, and so are dunders
        we do not recognise.
    """
    below = _below(cls.__mro__, stop)
    seen: set[str] = set()
    out: list[Binding] = []
    for owner in below:
        for name, raw in owner.__dict__.items():
            if name in seen or name in skip:
                continue
            if not _wanted(name, raw, include_dunders):
                continue
            seen.add(name)
            resolved = getattr(cls, name, raw)
            out.append(Binding(name=name, target=resolved, defining=owner, raw=raw))
    return tuple(out)


def _below(mro: tuple[type, ...], stop: type) -> tuple[type, ...]:
    """MRO segment strictly below ``stop``."""
    result: list[type] = []
    for cls in mro:
        if cls is stop:
            break
        result.append(cls)
    return tuple(result)


# Dunders that build a Nu term when invoked on a Form/Ref subclass.
# r-variants map to the same operator so we describe each operator once.
_OPERATOR_DUNDERS = frozenset(
    {
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__floordiv__",
        "__mod__",
        "__pow__",
        "__neg__",
        "__pos__",
        "__abs__",
        "__matmul__",
        "__invert__",
        "__lshift__",
        "__rshift__",
        "__and__",
        "__or__",
        "__xor__",
        "__gt__",
        "__lt__",
        "__ge__",
        "__le__",
        "__eq__",
        "__ne__",
        "__getitem__",
        "__setitem__",
        "__contains__",
        "__len__",
        "__iter__",
        "__call__",
    }
)


def _wanted(name: str, raw: object, include_dunders: bool) -> bool:
    """Whether this ``__dict__`` entry is a callable member we describe."""
    if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
        return False
    if name.startswith("__") and name.endswith("__"):
        if not include_dunders:
            return False
        if name not in _OPERATOR_DUNDERS:
            return False
    if isinstance(raw, (classmethod, staticmethod)):
        return callable(raw.__func__)
    if isinstance(raw, property):
        return False
    return callable(raw)
