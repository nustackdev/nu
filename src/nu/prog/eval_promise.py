"""Eval promise: declared expectations on an inner tree's attributes.

An Eval's carrier resolves to a Nu term whose shape is unknown at outer
compile time. A *promise* pins any subset of ``{sort, cardinality,
has_async_only_atom, has_sync_only_atom}`` on the payload; the runtime
validates the inner tree's actual attributes against each pinned field
and raises :class:`EvalPromiseError` on mismatch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.lang.attributes import Attr


if TYPE_CHECKING:
    from nu.engine.compilation import Program


__all__ = ["PROMISE_FIELDS", "PROMISE_KEY", "EvalPromiseError", "check_promise"]


# Payload key holding the promise dict on an Eval term. The string is shared
# vocabulary with ``nu.lang.attributes.cardinality`` (which reads the promise's
# cardinality field to refine CHILD_CARDINALITY without importing Eval).
PROMISE_KEY = "dyn_promise"


# Valid promise field names; a promise dict may hold any subset of these.
PROMISE_FIELDS = frozenset({"sort", "cardinality", "has_async_only_atom", "has_sync_only_atom"})


class EvalPromiseError(RuntimeError):
    """Raised when an Eval's resolved inner tree contradicts its declared promise."""


def check_promise(inner_program: Program, promise: dict[str, Any]) -> None:
    """Validate ``inner_program``'s root attributes against ``promise``.

    Fires per axis with a targeted message. A promise with no fields set is
    a no-op.
    """
    if not promise:
        return
    attrs = inner_program.attrs

    if "sort" in promise:
        # SORT is Declared; not stored in the attrs column store.
        actual = inner_program.attr((), Attr.SORT)
        expected = promise["sort"]
        # Sort match is exact or subsort ancestor: promise=SCALAR_QUERY accepts
        # SCALAR_QUERY and REDUCTION (subsort). Interior sorts (INTERACTION,
        # QUERY, ...) accept any descendant. Use subsort to reflect the tree.
        from nu.lang.attributes.sort import subsort

        if not subsort(actual, expected):
            msg = f"Eval promise mismatch on sort: expected {expected!r}, inner tree is {actual!r}"
            raise EvalPromiseError(msg)

    if "cardinality" in promise:
        actual = attrs[Attr.CHILD_CARDINALITY][0]
        expected = promise["cardinality"]
        if actual is not expected:
            msg = (
                f"Eval promise mismatch on cardinality: expected {expected!r}, "
                f"inner tree resolves to {actual!r}"
            )
            raise EvalPromiseError(msg)

    if "has_async_only_atom" in promise:
        actual = bool(attrs[Attr.HAS_ASYNC_ONLY_ATOM][0])
        expected = bool(promise["has_async_only_atom"])
        if actual != expected:
            msg = (
                f"Eval promise mismatch on has_async_only_atom: expected "
                f"{expected}, inner tree is {actual}"
            )
            raise EvalPromiseError(msg)

    if "has_sync_only_atom" in promise:
        actual = bool(attrs[Attr.HAS_SYNC_ONLY_ATOM][0])
        expected = bool(promise["has_sync_only_atom"])
        if actual != expected:
            msg = (
                f"Eval promise mismatch on has_sync_only_atom: expected "
                f"{expected}, inner tree is {actual}"
            )
            raise EvalPromiseError(msg)
