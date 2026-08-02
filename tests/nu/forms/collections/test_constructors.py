"""Tests for collection constructors — ``create()`` and ``Dict.of()``.

``create()`` yields a fresh empty container; ``Dict.of(**fields)`` builds a
dict from named field expressions. Both are pure scalar terms, so they run
through ``nu.run`` with no context.
"""

from __future__ import annotations

from nu import Dict, FrozenSet, Int, List, Set, Tuple, run


# --- create(): fresh empty containers ---------------------------------------


def test_create_yields_empty_containers() -> None:
    assert run(List.create())[0] == []
    assert run(Dict.create())[0] == {}
    assert run(Tuple.create())[0] == ()
    assert run(Set.create())[0] == set()
    assert run(FrozenSet.create())[0] == frozenset()


def test_mutable_create_yields_distinct_objects() -> None:
    # Equal by value, distinct by identity — a fresh object per evaluation.
    for form in (List, Dict, Set):
        a = run(form.create())[0]
        b = run(form.create())[0]
        assert a == b
        assert a is not b


# --- Dict.of(): dict from named fields -----------------------------------


def test_of_builds_dict_from_literals() -> None:
    got = run(Dict.of(a=1, b="two", c=[3, 4]))[0]
    assert got == {"a": 1, "b": "two", "c": [3, 4]}
    assert isinstance(got, dict)


def test_of_evaluates_nu_field_expressions() -> None:
    got = run(Dict.of(sum=Int(2) + Int(3), name="x"))[0]
    assert got == {"sum": 5, "name": "x"}


def test_of_accepts_spread_payload() -> None:
    payload = {"rows": [], "sort_column": "id"}
    assert run(Dict.of(**payload))[0] == payload


def test_of_with_no_fields_is_empty() -> None:
    assert run(Dict.of())[0] == {}
