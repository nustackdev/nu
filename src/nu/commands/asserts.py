"""Conditional-skip utility functions.

Composable helpers that return ``IfDo`` flow instances built from
duck-typed refs supporting ``.length()``, ``.exists()``, ``.missing()``.

The Assert family was removed in task-083; conditional checks via
SkipIf* helpers live on top of IfDo (a Control Flow).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from nu.terms.nu import NuBase as Nu

from nu.flows.control import IfDo


__all__ = [
    "SkipIfEmpty",
    "SkipIfExists",
    "SkipIfMissing",
    "SkipIfNotEmpty",
]


def SkipIfEmpty(  # noqa: N802
    ref: Any,  # noqa: ANN401
    child: Nu,
    else_: Nu | None = None,
) -> IfDo:
    """Execute *child* only if collection is NOT empty."""
    if else_ is not None:
        return IfDo(ref.length() > 0, child, else_)
    return IfDo(ref.length() > 0, child)


def SkipIfNotEmpty(  # noqa: N802
    ref: Any,  # noqa: ANN401
    child: Nu,
    else_: Nu | None = None,
) -> IfDo:
    """Execute *child* only if collection IS empty."""
    if else_ is not None:
        return IfDo(ref.length() == 0, child, else_)
    return IfDo(ref.length() == 0, child)


def SkipIfMissing(  # noqa: N802
    ref: Any,  # noqa: ANN401
    child: Nu,
    else_: Nu | None = None,
) -> IfDo:
    """Execute *child* only if ref's value exists."""
    if else_ is not None:
        return IfDo(ref.exists(), child, else_)
    return IfDo(ref.exists(), child)


def SkipIfExists(  # noqa: N802
    ref: Any,  # noqa: ANN401
    child: Nu,
    else_: Nu | None = None,
) -> IfDo:
    """Execute *child* only if ref's value is missing."""
    if else_ is not None:
        return IfDo(ref.missing(), child, else_)
    return IfDo(ref.missing(), child)
