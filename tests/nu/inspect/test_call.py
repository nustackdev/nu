"""Tests for nu.inspect.call - the callable kind, however it is reached.

Two ways in: off a class, through the MRO walk the builder kinds run, and off
a module, through the catalogue here. The record is the same either way.
"""

from __future__ import annotations

import nu.std.math as math_module
from nu.inspect import CallRecord, catalogue_calls, parse_call, parse_ref
from nu.mem.refs.items import IntRef


def _method(name: str) -> CallRecord:
    (record,) = [m for m in parse_ref(IntRef).methods if m.name == name]
    return record


# --- the receiver ---------------------------------------------------------


def test_self_is_the_receiver_and_not_an_argument() -> None:
    assert [a.name for a in _method("inc").args] == ["step"]
    assert [a.name for a in _method("__add__").args] == ["other"]


def test_a_classmethod_is_clean_the_same_way_a_method_is() -> None:
    record = parse_call(
        IntRef.slot,
        name="slot",
        path="nu.mem.IntRef.slot",
        owner="nu.mem.IntRef",
        binding="classmethod",
        qualifier="IntRef",
    )
    assert "cls" not in [a.name for a in record.args]


# --- the call form --------------------------------------------------------


def test_a_method_spells_with_its_real_arguments() -> None:
    record = _method("inc")
    assert record.spelling == ".inc(...)"
    assert record.call == ".inc(step=1)"


def test_an_operator_call_form_is_the_operator() -> None:
    assert _method("__add__").call == "a + b"


def test_a_free_function_call_form_carries_its_qualifier() -> None:
    (record,) = [r for r in catalogue_calls(math_module) if r.name == "sqrt"]
    assert record.call == "math.sqrt(x)"


# --- the catalogue --------------------------------------------------------


def test_a_std_module_of_free_functions_is_no_longer_empty() -> None:
    records = catalogue_calls(math_module)
    names = {r.name for r in records}
    assert {"sqrt", "sin", "gcd"} <= names
    assert all(r.binding == "function" for r in records)
    assert all(r.path.startswith("nu.std.math.") for r in records)


def test_the_catalogue_holds_no_constants_and_no_classes() -> None:
    names = {r.name for r in catalogue_calls(math_module)}
    assert not names & {"pi", "e", "tau", "inf", "nan"}
    assert all(
        callable(r.target) and not isinstance(r.target, type) for r in catalogue_calls(math_module)
    )


def test_a_call_record_knows_where_it_is_defined() -> None:
    (record,) = [r for r in catalogue_calls(math_module) if r.name == "sqrt"]
    assert record.module.startswith("nu.std.math")
    assert record.summary
