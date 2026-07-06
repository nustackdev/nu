# ruff: noqa: TC001
"""Task-119 typing tests: ``AnyForm`` behavior.

``AnyForm`` is the honest terminal - genuinely-unknown or dynamically-typed
values. It is absorbing under arithmetic + bitwise + subscript + attribute
descent (every op stays ``AnyForm``); comparison and logical ops yield
``BoolForm``. Protocol dunders (``len_()``, ``contains()``, ``iter_()``,
``bool_()``, ``has_attr()``) are exposed as named methods returning the
matching Form.

Reserved at the ``Nu`` base and deliberately absent: ``__and__`` / ``__or__``
(flow ops - ``Race`` / ``Parallel``); ``__call__`` (Nu runs through
interactions, not raw Python calls). Mutation dunders (``__setitem__`` /
``__delitem__``) are Ref-gated at build time.
"""

from __future__ import annotations

from typing import Any, assert_type

import nu
from nu.core import LiteralQuery
from nu.forms import AnyForm, BoolForm, IntForm, StrForm
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


# Primitive-blob subscripts narrow through the payload type_info (Phase 3).
assert_type(Blob.tags[0],     StrForm)
assert_type(Blob.scores[0],   IntForm)


# --- Two narrow operands compose narrowly ------------------------------


# IntRef + IntForm (from narrowed subscript) -> IntForm.
mixed = Blob.count + Blob.scores[0]
assert_type(mixed, IntForm)

# Well-typed alone stays narrow.
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


# --- Full absorbing arithmetic surface --------------------------------


assert_type(anyval + 1,         AnyForm)
assert_type(1 + anyval,         AnyForm)  # __radd__
assert_type(anyval - 1,         AnyForm)
assert_type(1 - anyval,         AnyForm)  # __rsub__
assert_type(anyval * 2,         AnyForm)
assert_type(2 * anyval,         AnyForm)  # __rmul__
assert_type(anyval / 2,         AnyForm)
assert_type(2 / anyval,         AnyForm)  # __rtruediv__
assert_type(anyval // 3,        AnyForm)
assert_type(3 // anyval,        AnyForm)  # __rfloordiv__
assert_type(anyval % 5,         AnyForm)
assert_type(5 % anyval,         AnyForm)  # __rmod__
assert_type(anyval ** 2,        AnyForm)
assert_type(2 ** anyval,        AnyForm)  # __rpow__
assert_type(anyval @ anyval,    AnyForm)  # __matmul__
assert_type(-anyval,            AnyForm)
assert_type(+anyval,            AnyForm)
assert_type(abs(anyval),        AnyForm)


# --- Absorbing bitwise surface ----------------------------------------


assert_type(anyval << 1,         AnyForm)
assert_type(1 << anyval,         AnyForm)  # __rlshift__
assert_type(anyval >> 1,         AnyForm)
assert_type(1 >> anyval,         AnyForm)  # __rrshift__
assert_type(anyval ^ 1,          AnyForm)
assert_type(1 ^ anyval,          AnyForm)  # __rxor__
assert_type(~anyval,             AnyForm)  # __invert__

# Named bitwise (& / | are reserved for flow ops).
assert_type(anyval.bitand(1),    AnyForm)
assert_type(anyval.bitor(1),     AnyForm)
assert_type(anyval.bitnot(),     AnyForm)


# --- Logical (named methods; & / | reserved for flow) ----------------


assert_type(anyval.and_(1),      BoolForm)
assert_type(anyval.or_(0),       BoolForm)
assert_type(anyval.not_(),       BoolForm)
assert_type(anyval.bool_(),      BoolForm)
assert_type(anyval.is_(anyval),  BoolForm)


# --- Dynamic descent: subscript ---------------------------------------


assert_type(anyval[0],           AnyForm)
assert_type(anyval["key"],       AnyForm)
assert_type(anyval[anyval],      AnyForm)   # ref-typed key
assert_type(anyval[1:3],         AnyForm)   # slice
assert_type(anyval[::2],         AnyForm)   # slice with step
assert_type(anyval[1:3][0],      AnyForm)   # chained
assert_type(anyval[0][1][2],     AnyForm)   # deep chain


# --- Dynamic descent: attribute ---------------------------------------


assert_type(anyval.field,            AnyForm)
assert_type(anyval.deeply.nested,    AnyForm)
assert_type(anyval.a.b.c.d,          AnyForm)
assert_type(anyval.field + 1,        AnyForm)   # composes with arithmetic
assert_type(anyval[0].field,         AnyForm)   # subscript then attr


# --- Named methods for protocol dunders -------------------------------


assert_type(anyval.len_(),       IntForm)
assert_type(anyval.contains(1),  BoolForm)
assert_type(anyval.has_attr("n"), BoolForm)
# iter_() -> IteratorForm (imported lazily; check via string)
from nu.forms import IteratorForm  # noqa: E402


assert_type(anyval.iter_(),      IteratorForm)


# --- Composing dynamic descent + arithmetic + comparison -------------


assert_type(anyval[0] + anyval[1],       AnyForm)
assert_type(anyval.a * anyval.b,         AnyForm)
assert_type(anyval.field > 0,            BoolForm)
assert_type((anyval[0] // 2).and_(1),    BoolForm)


# --- Mutation is Ref-gated at build time ------------------------------


# Positive tests only. Negative tests (value-node mutation raises
# TypeError at build time) live in ``test_negative_types.py`` since they
# are runtime-error assertions, not type-narrowing checks.
