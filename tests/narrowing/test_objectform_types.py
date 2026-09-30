# ruff: noqa: TC001
"""Task-119 typing tests: ``Object`` behavior.

``Object`` is the honest terminal - genuinely-unknown or dynamically-typed
values. It is absorbing under arithmetic + named bitwise + subscript + attribute
descent (every op stays ``Object``); comparison and logical ops yield
``Bool``. Protocol dunders (``len()``, ``contains()``, ``iter()``,
``bool_()``, ``has_attr()``) are exposed as named methods returning the
matching Form.

``&`` / ``|`` / ``>>`` compose flows on ``Object`` like on every term; bit,
set and merge operations are named methods. Deliberately absent: ``__call__`` (Nu runs through
interactions, not raw Python calls). Mutation dunders (``__setitem__`` /
``__delitem__``) are Ref-gated at build time.
"""

from __future__ import annotations

from typing import Any as PyAny

from typing_extensions import assert_type

import nu
import nustd
from nu.forms import Bool, Int, Object, Str
from nu.lang import Literal
from nustd.kv.refs import IntRef, PrimitiveListRef


# --- Constructing an Object ------------------------------------------


anyval: Object = Object(Literal(42))
assert_type(anyval, Object)


# --- Absorbing arithmetic --------------------------------------------


assert_type(anyval + 1, Object)
assert_type(anyval - 1, Object)
assert_type(anyval * 2, Object)
assert_type(anyval // 3, Object)
assert_type(anyval % 5, Object)
assert_type(anyval + anyval, Object)
assert_type((anyval + 1) * 2, Object)


# --- Absorbing comparison --------------------------------------------


# Object's comparison ops return Bool (well-typed decision even in
# the dynamic world).
assert_type(anyval > 0, Bool)
assert_type(anyval < 100, Bool)
assert_type(anyval == 42, Bool)
assert_type(anyval != 0, Bool)
assert_type(anyval >= 10, Bool)
assert_type(anyval <= 100, Bool)


# --- Sentinel checks (inherited from Form) ---------------------------


assert_type(anyval.is_empty(), Bool)
assert_type(anyval.is_invalid(), Bool)
assert_type(anyval.is_sentinel(), Bool)
assert_type(anyval.not_empty(), Bool)
assert_type(anyval.not_invalid(), Bool)


# --- Origin: primitive-blob subscript is Object today --------------


class Blob(nu.Shape):
    tags: PrimitiveListRef[str]
    scores: PrimitiveListRef[int]
    count: IntRef


# Primitive-blob subscripts narrow through the payload type_info (Phase 3).
assert_type(Blob.tags[0], Str)
assert_type(Blob.scores[0], Int)


# --- Two narrow operands compose narrowly ------------------------------


# IntRef + Int (from narrowed subscript) -> Int.
mixed = Blob.count + Blob.scores[0]
assert_type(mixed, Int)

# Well-typed alone stays narrow.
narrow = Blob.count + 1
assert_type(narrow, Int)


# --- Object from a literal Object ---------------------------------------


def _receive(x: PyAny) -> None:
    # If a user builds a Nu program with a plain-Object input, wrapping into
    # Object keeps the tree well-typed.
    wrapped: Object = Object(Literal(x))
    assert_type(wrapped, Object)
    assert_type(wrapped + 1, Object)
    assert_type(wrapped == 0, Bool)


# --- Full absorbing arithmetic surface --------------------------------


assert_type(anyval + 1, Object)
assert_type(1 + anyval, Object)  # __radd__
assert_type(anyval - 1, Object)
assert_type(1 - anyval, Object)  # __rsub__
assert_type(anyval * 2, Object)
assert_type(2 * anyval, Object)  # __rmul__
assert_type(anyval / 2, Object)
assert_type(2 / anyval, Object)  # __rtruediv__
assert_type(anyval // 3, Object)
assert_type(3 // anyval, Object)  # __rfloordiv__
assert_type(anyval % 5, Object)
assert_type(5 % anyval, Object)  # __rmod__
assert_type(anyval**2, Object)
assert_type(2**anyval, Object)  # __rpow__
assert_type(anyval @ anyval, Object)  # __matmul__
assert_type(-anyval, Object)
assert_type(+anyval, Object)
assert_type(abs(anyval), Object)


# --- Bitwise, set and merge: named methods ---------------------------


assert_type(anyval.bitand(1), Object)
assert_type(anyval.bitor(1), Object)
assert_type(anyval.bitxor(1), Object)
assert_type(anyval.bitnot(), Object)
assert_type(anyval.lshift(1), Object)
assert_type(anyval.rshift(1), Object)
assert_type(anyval.union({1}), Object)
assert_type(anyval.intersection({1}), Object)
assert_type(anyval.difference({1}), Object)
assert_type(anyval.symmetric_difference({1}), Object)
assert_type(anyval.merge({"a": 1}), Object)


# --- Logical (named methods; & / | compose flows on Object) --------


assert_type(anyval.and_(1), Bool)
assert_type(anyval.or_(0), Bool)
assert_type(anyval.not_(), Bool)
assert_type(anyval.bool_(), Bool)
assert_type(anyval.is_(anyval), Bool)


# --- Dynamic descent: subscript ---------------------------------------


assert_type(anyval[0], Object)
assert_type(anyval["key"], Object)
assert_type(anyval[anyval], Object)  # ref-typed key
assert_type(anyval[1:3], Object)  # slice
assert_type(anyval[::2], Object)  # slice with step
assert_type(anyval[1:3][0], Object)  # chained
assert_type(anyval[0][1][2], Object)  # deep chain


# --- Dynamic descent: attribute ---------------------------------------


assert_type(anyval.field, Object)
assert_type(anyval.deeply.nested, Object)
assert_type(anyval.a.b.c.d, Object)
assert_type(anyval.field + 1, Object)  # composes with arithmetic
assert_type(anyval[0].field, Object)  # subscript then attr


# --- Named methods for protocol dunders -------------------------------


assert_type(anyval.len(), Int)
assert_type(anyval.contains(1), Bool)
assert_type(anyval.has_attr("n"), Bool)
# iter_() -> Iterator (imported lazily; check via string)
from nu.forms import Iterator  # noqa: E402


assert_type(anyval.iter(), Iterator)


# --- Composing dynamic descent + arithmetic + comparison -------------


assert_type(anyval[0] + anyval[1], Object)
assert_type(anyval.a * anyval.b, Object)
assert_type(anyval.field > 0, Bool)
assert_type((anyval[0] // 2).and_(1), Bool)


# --- Mutation is Ref-gated at build time ------------------------------


# Positive tests only. Negative tests (value-node mutation raises
# TypeError at build time) live in ``test_negative_types.py`` since they
# are runtime-error assertions, not type-narrowing checks.


# --- Object slots into any narrow Arg via Object variance --------------


# Because Object is ``TypedNu[Object]`` (not ``TypedNu[object]``), it
# substitutes for ``Nu[int]`` / ``Nu[str]`` / ... via Python's Object
# variance rules. Concrete-typed refs consuming an Object keep their
# narrow return type instead of degrading through ``__radd__``.


class _S(nu.Shape):
    n: IntRef
    label: nustd.kv.StrRef


assert_type(_S.n + anyval, Int)
assert_type(_S.n - anyval, Int)
assert_type(_S.n * anyval, Int)
assert_type(_S.n // anyval, Int)
assert_type(_S.label + anyval, Str)
assert_type(anyval + _S.n, Object)  # __radd__ path stays Object-first
assert_type(_S.n > anyval, Bool)
assert_type(_S.label == anyval, Bool)
