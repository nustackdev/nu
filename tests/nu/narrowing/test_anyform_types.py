# ruff: noqa: TC001
"""Task-119 typing tests: ``AnyForm`` behavior.

``AnyForm`` is the honest terminal - genuinely-unknown or dynamically-typed
values. It is absorbing under arithmetic + comparison + logical ops (every
op stays ``AnyForm``), which is what lets ``computed_key // 2`` type-check
without exploding when the origin loses its narrowing.

Phase 4 will complete the dynamic-descent surface (``__getitem__``,
``__getattr__``, ``__iter__``, ``__call__``); tests here cover only what
exists today.
"""

from __future__ import annotations

from typing import Any, assert_type

import nu
from nu.core import LiteralQuery
from nu.forms import AnyForm, BoolForm, IntForm
from nu.virtuals.refs import IntRef, PrimitiveListRef


# --- Constructing an AnyForm ------------------------------------------


anyval: AnyForm = AnyForm(LiteralQuery(42))
assert_type(anyval, AnyForm)


# --- Absorbing arithmetic --------------------------------------------


assert_type(anyval + 1,        AnyForm)
assert_type(anyval - 1,        AnyForm)
assert_type(anyval * 2,        AnyForm)
assert_type(anyval // 3,       AnyForm)
assert_type(anyval % 5,        AnyForm)
assert_type(anyval + anyval,   AnyForm)
assert_type((anyval + 1) * 2,  AnyForm)


# --- Absorbing comparison --------------------------------------------


# AnyForm's comparison ops return BoolForm (well-typed decision even in
# the dynamic world).
assert_type(anyval > 0,     BoolForm)
assert_type(anyval < 100,   BoolForm)
assert_type(anyval == 42,   BoolForm)
assert_type(anyval != 0,    BoolForm)
assert_type(anyval >= 10,   BoolForm)
assert_type(anyval <= 100,  BoolForm)


# --- Sentinel checks (inherited from Form) ---------------------------


assert_type(anyval.is_empty(),     BoolForm)
assert_type(anyval.is_invalid(),   BoolForm)
assert_type(anyval.is_sentinel(),  BoolForm)
assert_type(anyval.not_empty(),    BoolForm)
assert_type(anyval.not_invalid(),  BoolForm)


# --- Origin: primitive-blob subscript is AnyForm today --------------


class Blob(nu.Shape):
    tags:   PrimitiveListRef[str]
    scores: PrimitiveListRef[int]
    count:  IntRef


# Origins that produce AnyForm today (Phase 3 target).
assert_type(Blob.tags[0],     AnyForm)  # FIXME(phase-3): -> StrForm
assert_type(Blob.scores[0],   AnyForm)  # FIXME(phase-3): -> IntForm


# --- AnyForm-in / AnyForm-out arithmetic mixing well-typed operands --


# An IntRef combined with an AnyForm degrades to AnyForm (AnyForm wins).
mixed = Blob.count + Blob.scores[0]
assert_type(mixed, AnyForm)  # FIXME(phase-3): -> IntForm

# But well-typed alone stays narrow.
narrow = Blob.count + 1
assert_type(narrow, IntForm)


# --- AnyForm from a literal Any ---------------------------------------


def _receive(x: Any) -> None:
    # If a user builds a Nu program with a plain-Any input, wrapping into
    # AnyForm keeps the tree well-typed.
    wrapped: AnyForm = AnyForm(LiteralQuery(x))
    assert_type(wrapped, AnyForm)
    assert_type(wrapped + 1, AnyForm)
    assert_type(wrapped == 0, BoolForm)


# --- Mypy-clean assignment of an AnyForm into a narrower slot fails --


# NOTE: negative tests live in ``test_negative_types.py``; keeping this
# file to POSITIVE + absorbing behaviour.
