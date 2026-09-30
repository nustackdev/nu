"""The ``==`` identity sweep.

Each class here used to answer ``==`` with a plain Python bool (object
identity). Now it builds ``Eq`` / ``Ne`` over the values, or raises when the
value has no equality to compare.
"""

from __future__ import annotations

import pytest

import nu
import nustd
import nustd.datetime as ndt
from nustd.cmath import complex as Complex  # noqa: N812
from nustd.decimal import Decimal
from nustd.fin import BasisPoint, Percentage
from nustd.fractions import Fraction
from nustd.pathlib import Path
from nustd.uuid import UUID


def _builds(result: object, atom: type) -> bool:
    return isinstance(result, nu.Bool) and isinstance(nu.tree.children(result)[0], atom)


def _check_builds(term: object) -> None:
    assert _builds(term == term, nu.Eq)
    assert _builds(term != term, nu.Ne)


# --- nu core -------------------------------------------------------------------


def test_none_compares_by_value() -> None:
    _check_builds(nu.None_())
    assert nu.run(nu.None_() == nu.None_())[0] is True
    assert nu.run(nu.None_() != 0)[0] is True


def test_iterator_has_no_value_equality() -> None:
    it = nu.List.of(1, 2).iter()
    with pytest.raises(TypeError, match=r"Iterator has no value equality.*to_list"):
        it == [1, 2]  # noqa: B015
    with pytest.raises(TypeError, match="Iterator has no value equality"):
        it != [1, 2]  # noqa: B015


def test_set_like_dict_views_compare_by_value() -> None:
    d = nu.Dict({"a": 1})
    _check_builds(d.keys())
    _check_builds(d.items())
    assert nu.run(d.keys() == {"a"})[0] is True
    assert nu.run(d.items() == {("a", 1)})[0] is True


def test_dict_values_view_has_no_value_equality() -> None:
    values = nu.Dict({"a": 1}).values()
    with pytest.raises(TypeError, match=r"values view has no value equality.*to_list"):
        values == [1]  # noqa: B015
    with pytest.raises(TypeError, match="values view has no value equality"):
        values != [1]  # noqa: B015
    assert nu.run(values.to_list() == [1])[0] is True


def test_program_compares_its_source() -> None:
    _check_builds(nu.Program("out = 1"))
    assert nu.run(nu.Program("out = 1") == "out = 1")[0] is True


# --- container refs ------------------------------------------------------------


class _Row(nu.Shape):
    a = nustd.kv.IntRef.slot()


class _Kv(nu.Shape):
    n = nustd.kv.IntRef.slot()
    xs = nustd.kv.ListRef.slot(int)
    d = nustd.kv.DictRef.slot(str, int)
    st = nustd.kv.SetRef.slot(int)
    rows = nustd.kv.ShapesListRef.slot(_Row)


class _Mem(nu.Shape):
    xs = nustd.mem.ListRef.slot(int)
    d = nustd.mem.DictRef.slot(str, int)
    st = nustd.mem.SetRef.slot(int)


@pytest.mark.parametrize(
    "ref",
    [_Kv.n, _Kv.xs, _Kv.d, _Kv.st, _Kv.rows, _Kv.rows[0], _Mem.xs, _Mem.d, _Mem.st],
    ids=lambda r: type(r).__name__,
)
def test_container_refs_build_comparisons(ref: object) -> None:
    _check_builds(ref)


def test_a_bare_item_ref_never_answers_with_a_python_bool() -> None:
    from nu.domains.shape.refs.item import ItemRef

    ref = ItemRef("x")
    assert isinstance(ref == 1, nu.Nu)
    assert isinstance(ref != 1, nu.Nu)


# --- nustd value forms ---------------------------------------------------------


STD = [
    (lambda: Decimal.of("1.5"), lambda: Decimal.of("1.50"), lambda: Decimal.of("2")),
    (lambda: Fraction.of(1, 2), lambda: Fraction.of(2, 4), lambda: Fraction.of(1, 3)),
    (lambda: Complex.of(1, 2), lambda: Complex.of(1, 2), lambda: Complex.of(2, 1)),
    (lambda: Path.of("a", "b"), lambda: Path.of("a/b"), lambda: Path.of("a")),
    (
        lambda: UUID.from_int(1),
        lambda: UUID.from_str("00000000-0000-0000-0000-000000000001"),
        lambda: UUID.from_int(2),
    ),
    (
        lambda: ndt.date.of(2026, 1, 1),
        lambda: ndt.date.of(2026, 1, 1),
        lambda: ndt.date.of(2026, 1, 2),
    ),
    (
        lambda: ndt.datetime.of(2026, 1, 1, hour=3),
        lambda: ndt.datetime.of(2026, 1, 1, hour=3),
        lambda: ndt.datetime.of(2026, 1, 1),
    ),
    (lambda: ndt.time.of(hour=3), lambda: ndt.time.of(hour=3), lambda: ndt.time.of(hour=4)),
    (
        lambda: ndt.timedelta.of(days=1),
        lambda: ndt.timedelta.of(hours=24),
        lambda: ndt.timedelta.of(),
    ),
    (
        lambda: ndt.timezone.utc(),
        lambda: ndt.timezone.utc(),
        lambda: ndt.timezone.of(ndt.timedelta.of(hours=1)),
    ),
    (lambda: Percentage.of(10.0), lambda: Percentage.of(10.0), lambda: Percentage.of(20.0)),
    (lambda: BasisPoint.of(5), lambda: BasisPoint.of(5), lambda: BasisPoint.of(6)),
]


@pytest.mark.parametrize(("make", "same", "other"), STD, ids=lambda f: "")
def test_std_forms_compare_by_value(make: object, same: object, other: object) -> None:
    a, b, c = make(), same(), other()  # type: ignore[operator]
    _check_builds(a)
    assert nu.run(a == b)[0] is True
    assert nu.run(a == c)[0] is False
    assert nu.run(a != c)[0] is True
