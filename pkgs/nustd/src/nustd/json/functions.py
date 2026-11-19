"""Module-level functions for ``nustd.json``.

``json`` has no central class, so this is the whole surface: typed wrappers
that mirror ``json.loads`` / ``json.dumps``. Each wrapper builds its
interaction atom (lazily imported, like ``nustd.math``) and returns the Form
that matches the host return type:

- ``loads`` -> ``Object`` (a JSON document can be any of dict, list, str,
  int, float, bool or None, so the type is only known at run time)
- ``dumps`` -> ``Str``

Options left as ``None`` are not passed, so the stdlib default applies.
Callable options (``default``, ``cls``, ``object_hook``, ``parse_float`` ...)
are not offered: a callable is not a value a Nu tree carries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms import Object, Str


if TYPE_CHECKING:
    from nu.lang import Arg, BoolArg, IntArg, StrArg, TupleArg


__all__ = [
    "dumps",
    "loads",
]


def loads(s: StrArg | Arg[bytes]) -> Object:
    """Parse the JSON document ``s`` into a Python value: mirrors ``json.loads()``.

    Bad input raises ``JSONDecodeError`` when the tree runs.
    """
    from .interactions import JsonLoads

    return Object(JsonLoads(s))


def dumps(
    obj: object,
    *,
    indent: IntArg | StrArg | None = None,
    sort_keys: BoolArg | None = None,
    separators: TupleArg[str, str] | None = None,
    ensure_ascii: BoolArg | None = None,
) -> Str:
    """Serialize ``obj`` to a JSON string: mirrors ``json.dumps()``.

    A value JSON can't encode raises ``TypeError`` when the tree runs.
    """
    from .interactions import JsonDumps

    kw: dict[str, object] = {}
    if indent is not None:
        kw["indent"] = indent
    if sort_keys is not None:
        kw["sort_keys"] = sort_keys
    if separators is not None:
        kw["separators"] = separators
    if ensure_ascii is not None:
        kw["ensure_ascii"] = ensure_ascii
    return Str(JsonDumps(obj, **kw))
