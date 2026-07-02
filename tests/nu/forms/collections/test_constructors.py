"""Tests for collection constructors — ``create()`` and ``DictForm.of()``.

``create()`` yields a fresh empty container; ``DictForm.of(**fields)`` builds a
dict from named field expressions. Both are pure scalar terms, so they run
through ``nu.run`` with no context.
"""

from __future__ import annotations

from nu import DictForm, FrozenSetForm, IntForm, ListForm, SetForm, TupleForm, run


# --- create(): fresh empty containers ---------------------------------------


def test_create_yields_empty_containers() -> None:
    assert run(ListForm.create())[0] == []
    assert run(DictForm.create())[0] == {}
    assert run(TupleForm.create())[0] == ()
    assert run(SetForm.create())[0] == set()
    assert run(FrozenSetForm.create())[0] == frozenset()


def test_mutable_create_yields_distinct_objects() -> None:
    # Equal by value, distinct by identity — a fresh object per evaluation.
    for form in (ListForm, DictForm, SetForm):
        a = run(form.create())[0]
        b = run(form.create())[0]
        assert a == b
        assert a is not b


# --- DictForm.of(): dict from named fields -----------------------------------


def test_of_builds_dict_from_literals() -> None:
    got = run(DictForm.of(a=1, b="two", c=[3, 4]))[0]
    assert got == {"a": 1, "b": "two", "c": [3, 4]}
    assert isinstance(got, dict)


def test_of_evaluates_nu_field_expressions() -> None:
    got = run(DictForm.of(sum=IntForm(2) + IntForm(3), name="x"))[0]
    assert got == {"sum": 5, "name": "x"}


def test_of_accepts_spread_payload() -> None:
    payload = {"rows": [], "sort_column": "id"}
    assert run(DictForm.of(**payload))[0] == payload


def test_of_with_no_fields_is_empty() -> None:
    assert run(DictForm.of())[0] == {}
