"""The operator rule, per Form.

``&``, ``|`` and ``>>`` are flow composition (Race, Parallel, Sequential) on
every term. A Form whose Python type defines one of them overrides it with the
Python meaning; where Python has no such operator for the type it stays flow.
"""

from __future__ import annotations

import pytest

import nu
import nustd.datetime as ndt
from nu.core import BitAnd, BitNot, BitOr, LShift, RShift
from nu.core.logical import And, Or
from nu.forms.collections.abc.mapping_interactions import Merge, MergeUpdate
from nu.forms.collections.abc.set_interactions import SetAnd, SetIOr, SetOr
from nustd.decimal import Decimal


def atom(term: object) -> type:
    """The interaction an operator built, under the Form that wraps it."""
    if isinstance(term, nu.Form):
        return type(nu.tree.children(term)[0])
    return type(term)


FLOW = {"&": nu.Race, "|": nu.Parallel, ">>": nu.Sequential}

# (name, build a term, {operator: the atom it must build})
RULE = [
    ("Object", lambda: nu.Object(12), {"&": BitAnd, "|": BitOr, ">>": RShift}),
    ("Int", lambda: nu.Int(12), {"&": BitAnd, "|": BitOr, ">>": RShift}),
    ("IntAttrRef", lambda: nu.IntAttrRef("n"), {"&": BitAnd, "|": BitOr, ">>": RShift}),
    ("Bool", lambda: nu.Int(1) > 0, {"&": And, "|": Or, ">>": nu.Sequential}),
    ("Set", lambda: nu.Set({1, 2}), {"&": SetAnd, "|": SetOr, ">>": nu.Sequential}),
    ("FrozenSet", lambda: nu.FrozenSet(frozenset({1})), {"&": SetAnd, "|": SetOr}),
    ("DictKeys", lambda: nu.Dict({"a": 1}).keys(), {"&": SetAnd, "|": SetOr}),
    ("Dict", lambda: nu.Dict({"a": 1}), {"&": nu.Race, "|": Merge, ">>": nu.Sequential}),
    ("Float", lambda: nu.Float(1.5), FLOW),
    ("Str", lambda: nu.Str("a"), FLOW),
    ("Bytes", lambda: nu.Bytes(b"a"), FLOW),
    ("None_", lambda: nu.None_(), FLOW),
    ("List", lambda: nu.List.of(1), FLOW),
    ("Tuple", lambda: nu.Tuple.of(1), FLOW),
    ("DictValues", lambda: nu.Dict({"a": 1}).values(), FLOW),
    ("Decimal", lambda: Decimal.of("1"), FLOW),
    ("date", lambda: ndt.date.of(2026, 1, 1), FLOW),
    ("Add", lambda: nu.Add(1, 2), FLOW),
]

OPS = {
    "&": lambda a, b: a & b,
    "|": lambda a, b: a | b,
    ">>": lambda a, b: a >> b,
}


@pytest.mark.parametrize(
    ("name", "build", "op", "expected"),
    [(name, build, op, exp) for name, build, table in RULE for op, exp in table.items()],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_operator_rule(name: str, build: object, op: str, expected: type) -> None:
    other = build()  # type: ignore[operator]
    assert atom(OPS[op](build(), other)) is expected  # type: ignore[operator]


def test_int_keeps_every_python_bit_operator() -> None:
    assert nu.run(nu.Int(0b1100) & 0b1010)[0] == 8
    assert nu.run(0b1100 & nu.Int(0b1010))[0] == 8
    assert nu.run(nu.Int(0b1100) | 0b1010)[0] == 14
    assert nu.run(0b1100 | nu.Int(0b1010))[0] == 14
    assert nu.run(nu.Int(16) >> 2)[0] == 4
    assert nu.run(nu.Int(1) << 4)[0] == 16
    assert nu.run(~nu.Int(5))[0] == -6
    assert atom(~nu.Int(5)) is BitNot
    assert atom(nu.Int(1) << 4) is LShift


def test_object_keeps_every_python_operator_including_reflected() -> None:
    assert nu.run(nu.Object(12) & 10)[0] == 8
    assert nu.run(12 & nu.Object(10))[0] == 8
    assert nu.run(nu.Object(12) | 10)[0] == 14
    assert nu.run(12 | nu.Object(10))[0] == 14
    assert nu.run(nu.Object({1, 2}) & {2, 3})[0] == {2}
    assert nu.run(16 >> nu.Object(2))[0] == 4


def test_bool_and_or_are_logical() -> None:
    assert nu.run((nu.Int(3) > 2) & (nu.Int(3) < 5))[0] is True
    assert nu.run((nu.Int(3) > 5) | (nu.Int(3) < 5))[0] is True
    assert nu.run(True & nu.Bool(False))[0] is False
    assert nu.run(False | nu.Bool(True))[0] is True


def test_dict_pipe_merges() -> None:
    assert nu.run(nu.Dict({"a": 1}) | {"b": 2})[0] == {"a": 1, "b": 2}
    assert nu.run({"a": 1} | nu.Dict({"a": 2}))[0] == {"a": 2}
    d = nu.Dict({"a": 1})
    d |= {"b": 2}
    assert atom(d) is MergeUpdate
    assert nu.run(d)[0] == {"a": 1, "b": 2}


def test_set_in_place_union_stays_set_algebra() -> None:
    s = nu.Set({1})
    s |= {2}
    assert atom(s) is SetIOr


def test_flows_still_compose_with_and_or_then() -> None:
    step = nu.print("x")
    assert isinstance(step >> step, nu.Sequential)
    assert isinstance(step | step, nu.Parallel)
    assert isinstance(step & step, nu.Race)
