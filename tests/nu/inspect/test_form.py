"""Tests for nu.inspect.form - FormRecord over BuilderRecord."""

from __future__ import annotations

from nu.forms import Bool, Int, Str
from nu.inspect import BuilderRecord, FormRecord, parse_form, verify_form


def test_a_form_is_a_builder_record_dispatch_tagged() -> None:
    record = parse_form(Int)
    assert isinstance(record, FormRecord)
    assert isinstance(record, BuilderRecord)
    assert record.name == "Int"
    assert record.methods, "expected the operator + logical surface"


def test_int_carries_the_full_operator_surface() -> None:
    spellings = {m.spelling for m in parse_form(Int).methods}
    assert {"a + b", "a - b", "a * b", "a / b", "a > b", "a == b"} <= spellings


def test_other_primitive_forms_parse_too() -> None:
    assert parse_form(Str).name == "Str"
    assert parse_form(Bool).name == "Bool"


def test_int_docstrings_are_clean_by_the_shared_laws() -> None:
    assert verify_form(Int) == []
