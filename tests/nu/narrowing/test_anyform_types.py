# ruff: noqa: TC001
"""Task-119 typing tests: ``Any`` behavior.

``Any`` is the honest terminal - genuinely-unknown or dynamically-typed
values. It is absorbing under arithmetic + bitwise + subscript + attribute
descent (every op stays ``Any``); comparison and logical ops yield
``Bool``. Protocol dunders (``len_()``, ``contains()``, ``iter_()``,
``bool_()``, ``has_attr()``) are exposed as named methods returning the
matching Form.

Reserved at the ``Nu`` base and deliberately absent: ``__and__`` / ``__or__``
(flow ops - ``Race`` / ``Parallel``); ``__call__`` (Nu runs through
interactions, not raw Python calls). Mutation dunders (``__setitem__`` /
``__delitem__``) are Ref-gated at build time.
"""

from __future__ import annotations

from typing import Any as PyAny

from typing_extensions import assert_type

import nu
from nu.core import Literal
from nu.forms import Any, Bool, Int, Str
from nu.virtuals.refs import IntRef, PrimitiveListRef


# --- Constructing an Any ------------------------------------------


anyval: Any = Any(Literal(42))
assert_type(anyval, Any)


# --- Absorbing arithmetic --------------------------------------------


assert_type(anyval + 1, Any)
assert_type(anyval - 1, Any)
assert_type(anyval * 2, Any)
assert_type(anyval // 3, Any)
assert_type(anyval % 5, Any)
assert_type(anyval + anyval, Any)
assert_type((anyval + 1) * 2, Any)


# --- Absorbing comparison --------------------------------------------


# Any's comparison ops return Bool (well-typed decision even in
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


# --- Origin: primitive-blob subscript is Any today --------------


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


# --- Any from a literal Any ---------------------------------------


def _receive(x: PyAny) -> None:
    # If a user builds a Nu program with a plain-Any input, wrapping into
    # Any keeps the tree well-typed.
    wrapped: Any = Any(Literal(x))
    assert_type(wrapped, Any)
    assert_type(wrapped + 1, Any)
    assert_type(wrapped == 0, Bool)


# --- Full absorbing arithmetic surface --------------------------------


assert_type(anyval + 1, Any)
assert_type(1 + anyval, Any)  # __radd__
assert_type(anyval - 1, Any)
assert_type(1 - anyval, Any)  # __rsub__
assert_type(anyval * 2, Any)
assert_type(2 * anyval, Any)  # __rmul__
assert_type(anyval / 2, Any)
assert_type(2 / anyval, Any)  # __rtruediv__
assert_type(anyval // 3, Any)
assert_type(3 // anyval, Any)  # __rfloordiv__
assert_type(anyval % 5, Any)
assert_type(5 % anyval, Any)  # __rmod__
assert_type(anyval**2, Any)
assert_type(2**anyval, Any)  # __rpow__
assert_type(anyval @ anyval, Any)  # __matmul__
assert_type(-anyval, Any)
assert_type(+anyval, Any)
assert_type(abs(anyval), Any)


# --- Absorbing bitwise surface ----------------------------------------


assert_type(anyval << 1, Any)
assert_type(1 << anyval, Any)  # __rlshift__
assert_type(anyval >> 1, Any)
assert_type(1 >> anyval, Any)  # __rrshift__
assert_type(anyval ^ 1, Any)
assert_type(1 ^ anyval, Any)  # __rxor__
assert_type(~anyval, Any)  # __invert__

# Named bitwise (& / | are reserved for flow ops).
assert_type(anyval.bitand(1), Any)
assert_type(anyval.bitor(1), Any)
assert_type(anyval.bitnot(), Any)


# --- Logical (named methods; & / | reserved for flow) ----------------


assert_type(anyval.and_(1), Bool)
assert_type(anyval.or_(0), Bool)
assert_type(anyval.not_(), Bool)
assert_type(anyval.bool_(), Bool)
assert_type(anyval.is_(anyval), Bool)


# --- Dynamic descent: subscript ---------------------------------------


assert_type(anyval[0], Any)
assert_type(anyval["key"], Any)
assert_type(anyval[anyval], Any)  # ref-typed key
assert_type(anyval[1:3], Any)  # slice
assert_type(anyval[::2], Any)  # slice with step
assert_type(anyval[1:3][0], Any)  # chained
assert_type(anyval[0][1][2], Any)  # deep chain


# --- Dynamic descent: attribute ---------------------------------------


assert_type(anyval.field, Any)
assert_type(anyval.deeply.nested, Any)
assert_type(anyval.a.b.c.d, Any)
assert_type(anyval.field + 1, Any)  # composes with arithmetic
assert_type(anyval[0].field, Any)  # subscript then attr


# --- Named methods for protocol dunders -------------------------------


assert_type(anyval.len_(), Int)
assert_type(anyval.contains(1), Bool)
assert_type(anyval.has_attr("n"), Bool)
# iter_() -> Iterator (imported lazily; check via string)
from nu.forms import Iterator  # noqa: E402


assert_type(anyval.iter_(), Iterator)


# --- Composing dynamic descent + arithmetic + comparison -------------


assert_type(anyval[0] + anyval[1], Any)
assert_type(anyval.a * anyval.b, Any)
assert_type(anyval.field > 0, Bool)
assert_type((anyval[0] // 2).and_(1), Bool)


# --- Mutation is Ref-gated at build time ------------------------------


# Positive tests only. Negative tests (value-node mutation raises
# TypeError at build time) live in ``test_negative_types.py`` since they
# are runtime-error assertions, not type-narrowing checks.


# --- Any slots into any narrow Arg via Any variance --------------


# Because Any is ``TypedNu[Any]`` (not ``TypedNu[object]``), it
# substitutes for ``Nu[int]`` / ``Nu[str]`` / ... via Python's Any
# variance rules. Concrete-typed refs consuming an Any keep their
# narrow return type instead of degrading through ``__radd__``.


class _S(nu.Shape):
    n: IntRef
    label: nu.kv.StrRef


assert_type(_S.n + anyval, Int)
assert_type(_S.n - anyval, Int)
assert_type(_S.n * anyval, Int)
assert_type(_S.n // anyval, Int)
assert_type(_S.label + anyval, Str)
assert_type(anyval + _S.n, Any)  # __radd__ path stays Any-first
assert_type(_S.n > anyval, Bool)
assert_type(_S.label == anyval, Bool)
