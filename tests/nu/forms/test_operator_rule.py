"""The operator rule.

``&``, ``|`` and ``>>`` build Race, Parallel and Sequential on every term,
reflected versions included, and no form overrides them. The other bitwise and
set operators (``<< ^ ~``, set ``- ^``) are not defined on forms at all. The
value versions are named methods, and each builds its own interaction.
"""

from __future__ import annotations

import pytest

import nu
import nustd
import nustd.datetime as ndt
from nu.core import BitAnd, BitNot, BitOr, BitXor, LShift, RShift
from nu.core.logical import And, Not, Or
from nu.engine.validation import ValidationError
from nu.forms.collections.abc.mapping_interactions import Merge, MergeUpdate
from nu.forms.collections.abc.set_interactions import (
    Difference,
    Intersection,
    SymmetricDifference,
    Union,
)
from nustd.decimal import Decimal
from nustd.mem.refs.jqueue import JQueueRef


class _Row(nu.Shape):
    a = nustd.kv.IntRef.slot()


class _Kv(nu.Shape):
    n = nustd.kv.IntRef.slot()
    xs = nustd.kv.ListRef.slot(int)
    d = nustd.kv.DictRef.slot(int)
    st = nustd.kv.SetRef.slot(int)
    rows = nustd.kv.ListRef.slot(_Row)
    row = nustd.kv.ShapeRef.slot(_Row)
    pd: nustd.kv.PrimitiveDictRef[str, int]
    ps: nustd.kv.PrimitiveSetRef[int]


class _Mem(nu.Shape):
    n = nustd.mem.IntRef.slot()
    xs = nustd.mem.ListRef.slot(int)
    d = nustd.mem.DictRef.slot(int)
    st = nustd.mem.SetRef.slot(int)
    q = JQueueRef.slot(item_type=int)


# (name, build a term): every family of form, value and ref alike.
TERMS = [
    ("Object", lambda: nu.Object(12)),
    ("Int", lambda: nu.Int(12)),
    ("IntAttrRef", lambda: nu.IntAttrRef("n")),
    ("Bool", lambda: nu.Int(1) > 0),
    ("Float", lambda: nu.Float(1.5)),
    ("Str", lambda: nu.Str("a")),
    ("Bytes", lambda: nu.Bytes(b"a")),
    ("None_", lambda: nu.None_()),
    ("List", lambda: nu.List.of(1)),
    ("Tuple", lambda: nu.Tuple.of(1)),
    ("Set", lambda: nu.Set({1, 2})),
    ("FrozenSet", lambda: nu.FrozenSet(frozenset({1}))),
    ("Dict", lambda: nu.Dict({"a": 1})),
    ("DictKeys", lambda: nu.Dict({"a": 1}).keys()),
    ("DictItems", lambda: nu.Dict({"a": 1}).items()),
    ("DictValues", lambda: nu.Dict({"a": 1}).values()),
    ("Iterator", lambda: nu.List.of(1).iter()),
    ("Decimal", lambda: Decimal.of("1")),
    ("date", lambda: ndt.date.of(2026, 1, 1)),
    ("Add", lambda: nu.Add(1, 2)),
    ("kv.IntRef", lambda: _Kv.n),
    ("kv.ListRef", lambda: _Kv.xs),
    ("kv.DictRef", lambda: _Kv.d),
    ("kv.SetRef", lambda: _Kv.st),
    ("kv.ListRef", lambda: _Kv.rows),
    ("kv.ShapeRef", lambda: _Kv.row),
    ("kv.PrimitiveDictRef", lambda: _Kv.pd),
    ("kv.PrimitiveSetRef", lambda: _Kv.ps),
    ("mem.IntRef", lambda: _Mem.n),
    ("mem.ListRef", lambda: _Mem.xs),
    ("mem.DictRef", lambda: _Mem.d),
    ("mem.SetRef", lambda: _Mem.st),
    ("mem.JQueueRef", lambda: _Mem.q),
]

FLOWS = [
    ("&", lambda a, b: a & b, nu.Race),
    ("|", lambda a, b: a | b, nu.Parallel),
    (">>", lambda a, b: a >> b, nu.Sequential),
]


@pytest.mark.parametrize(("name", "build"), TERMS, ids=[n for n, _ in TERMS])
@pytest.mark.parametrize(("op", "apply", "flow"), FLOWS, ids=[o for o, _, _ in FLOWS])
def test_flow_operators_compose_on_every_term(
    name: str, build: object, op: str, apply: object, flow: type
) -> None:
    a, b = build(), build()  # type: ignore[operator]
    result = apply(a, b)  # type: ignore[operator]
    assert type(result) is flow
    assert nu.tree.children(result)[0] is a
    assert nu.tree.children(result)[1] is b


@pytest.mark.parametrize(("name", "build"), TERMS, ids=[n for n, _ in TERMS])
def test_reflected_flow_operators_compose_too(name: str, build: object) -> None:
    term = build()  # type: ignore[operator]
    race = 2 & term
    assert type(race) is nu.Race
    assert nu.tree.children(race)[1] is term
    seq = 2 >> term
    assert type(seq) is nu.Sequential
    assert nu.tree.children(seq)[1] is term
    # `|` reflected builds a Parallel too; Parallel itself refuses a bare
    # Python value as a branch, so the error is Parallel's, never a union.
    with pytest.raises(TypeError, match="Parallel child must be a Nu"):
        {2} | term


def test_int_and_builds_a_race_the_validator_judges() -> None:
    race = nu.Int(1) & 2
    assert type(race) is nu.Race
    with pytest.raises(ValidationError):
        nu.run(race)


@pytest.mark.parametrize(
    ("name", "apply"),
    [
        ("Int <<", lambda: nu.Int(1) << 2),
        ("Int ^", lambda: nu.Int(1) ^ 2),
        ("Int ~", lambda: ~nu.Int(1)),
        ("int << Int", lambda: 1 << nu.Int(2)),
        ("Object <<", lambda: nu.Object(1) << 2),
        ("Object ^", lambda: nu.Object(1) ^ 2),
        ("Object ~", lambda: ~nu.Object(1)),
        ("Set -", lambda: nu.Set({1}) - {1}),
        ("Set ^", lambda: nu.Set({1}) ^ {1}),
        ("set - Set", lambda: {1} - nu.Set({1})),
        ("DictKeys -", lambda: nu.Dict({"a": 1}).keys() - {"a"}),
        ("SetRef ^", lambda: _Mem.st ^ {1}),
    ],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_other_bit_and_set_operators_are_not_defined(name: str, apply: object) -> None:
    with pytest.raises(TypeError, match=r"unsupported operand|bad operand"):
        apply()  # type: ignore[operator]


def test_arithmetic_stays_an_operator() -> None:
    assert nu.run(nu.Int(5) - 2)[0] == 3
    assert nu.run(-nu.Int(5))[0] == -5
    assert nu.run(nu.Object(7) - 2)[0] == 5


# --- the value versions are named methods -----------------------------------------

# (name, build the call, the atom it must build, what it runs to)
METHODS = [
    ("Bool.and_", lambda: nu.Bool(True).and_(False), And, False),
    ("Bool.or_", lambda: nu.Bool(False).or_(True), Or, True),
    ("Bool.not_", lambda: nu.Bool(True).not_(), Not, False),
    ("Int.bitand", lambda: nu.Int(0b1100).bitand(0b1010), BitAnd, 8),
    ("Int.bitor", lambda: nu.Int(0b1100).bitor(0b1010), BitOr, 14),
    ("Int.bitxor", lambda: nu.Int(0b1100).bitxor(0b1010), BitXor, 6),
    ("Int.bitnot", lambda: nu.Int(5).bitnot(), BitNot, -6),
    ("Int.lshift", lambda: nu.Int(1).lshift(4), LShift, 16),
    ("Int.rshift", lambda: nu.Int(16).rshift(2), RShift, 4),
    ("Set.intersection", lambda: nu.Set({1, 2}).intersection({2, 3}), Intersection, {2}),
    ("Set.union", lambda: nu.Set({1}).union({2}), Union, {1, 2}),
    ("Set.difference", lambda: nu.Set({1, 2}).difference({2}), Difference, {1}),
    (
        "Set.symmetric_difference",
        lambda: nu.Set({1, 2}).symmetric_difference({2, 3}),
        SymmetricDifference,
        {1, 3},
    ),
    ("FrozenSet.union", lambda: nu.FrozenSet(frozenset({1})).union({2}), Union, {1, 2}),
    ("DictKeys.union", lambda: nu.Dict({"a": 1}).keys().union({"b"}), Union, {"a", "b"}),
    ("Dict.merge", lambda: nu.Dict({"a": 1}).merge({"b": 2}), Merge, {"a": 1, "b": 2}),
    (
        "Dict.merge_update",
        lambda: nu.Dict({"a": 1}).merge_update({"b": 2}),
        MergeUpdate,
        {"a": 1, "b": 2},
    ),
    ("Object.and_", lambda: nu.Object(1).and_(0), And, False),
    ("Object.or_", lambda: nu.Object(0).or_(1), Or, True),
    ("Object.not_", lambda: nu.Object(0).not_(), Not, True),
    ("Object.bitand", lambda: nu.Object(12).bitand(10), BitAnd, 8),
    ("Object.bitor", lambda: nu.Object(12).bitor(10), BitOr, 14),
    ("Object.bitxor", lambda: nu.Object(12).bitxor(10), BitXor, 6),
    ("Object.bitnot", lambda: nu.Object(5).bitnot(), BitNot, -6),
    ("Object.lshift", lambda: nu.Object(1).lshift(4), LShift, 16),
    ("Object.rshift", lambda: nu.Object(16).rshift(2), RShift, 4),
    ("Object.bitand on sets", lambda: nu.Object({1, 2}).bitand({2}), BitAnd, {2}),
    ("Object.bitor on dicts", lambda: nu.Object({"a": 1}).bitor({"b": 2}), BitOr, {"a": 1, "b": 2}),
    ("Object.union", lambda: nu.Object({1}).union({2}), Union, {1, 2}),
    ("Object.intersection", lambda: nu.Object({1, 2}).intersection({2}), Intersection, {2}),
    ("Object.difference", lambda: nu.Object({1, 2}).difference({2}), Difference, {1}),
    (
        "Object.symmetric_difference",
        lambda: nu.Object({1, 2}).symmetric_difference({2, 3}),
        SymmetricDifference,
        {1, 3},
    ),
    ("Object.merge", lambda: nu.Object({"a": 1}).merge({"b": 2}), Merge, {"a": 1, "b": 2}),
    (
        "Object.merge_update",
        lambda: nu.Object({"a": 1}).merge_update({"b": 2}),
        MergeUpdate,
        {"a": 1, "b": 2},
    ),
]


@pytest.mark.parametrize(
    ("name", "build", "expected", "value"), METHODS, ids=[m[0] for m in METHODS]
)
def test_each_method_builds_its_interaction(
    name: str, build: object, expected: type, value: object
) -> None:
    term = build()  # type: ignore[operator]
    assert type(nu.tree.children(term)[0]) is expected
    assert nu.run(term)[0] == value


def test_set_methods_take_plain_sets_and_forms_on_the_right() -> None:
    s = nu.Set({1, 2})
    assert nu.run(s.union({3}))[0] == {1, 2, 3}
    assert nu.run(s.union(frozenset({3})))[0] == {1, 2, 3}
    assert nu.run(s.union(nu.Set({3})))[0] == {1, 2, 3}
    assert nu.run(s.intersection(nu.Dict({2: "x"}).keys()))[0] == {2}
    assert nu.run(nu.Dict({"a": 1}).keys().difference({"a"}))[0] == set()
    assert nu.run(s.issubset({1, 2, 3}))[0] is True
    # A plain set on the left: the interaction itself takes either side.
    assert nu.run(Union({1}, s))[0] == {1, 2}
    assert nu.run(Difference({1, 2, 3}, s))[0] == {3}


@pytest.mark.parametrize(
    ("ref", "method", "arg", "expected"),
    [
        (_Kv.st, "union", {1}, Union),
        (_Kv.st, "intersection", {1}, Intersection),
        (_Mem.st, "difference", {1}, Difference),
        (_Mem.st, "symmetric_difference", {1}, SymmetricDifference),
        (_Kv.ps, "union", {1}, Union),
        (_Kv.d, "merge", {"a": 1}, Merge),
        (_Mem.d, "merge", {"a": 1}, Merge),
        (_Kv.pd, "merge", {"a": 1}, Merge),
        (_Kv.n, "bitand", 1, BitAnd),
        (_Mem.n, "lshift", 1, LShift),
    ],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_container_refs_carry_the_methods(
    ref: object, method: str, arg: object, expected: type
) -> None:
    term = getattr(ref, method)(arg)
    assert type(nu.tree.children(term)[0]) is expected


def test_mutating_set_and_merge_methods_run_on_a_ref() -> None:
    ctx = nu.Context().bind(dict, {"st": {1}, "d": {"a": 1}}, _Mem)
    _, ctx = nu.run(_Mem.st.update({2}), ctx)
    assert nu.run(_Mem.d.merge_update({"b": 2}), ctx)[0] == {"a": 1, "b": 2}
    assert nu.run(_Mem.st, ctx)[0] == {1, 2}
    assert nu.run(_Mem.d, ctx)[0] == {"a": 1, "b": 2}
