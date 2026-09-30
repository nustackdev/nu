"""Tests for nu.inspect.ref - RefRecord over BuilderRecord."""

from __future__ import annotations

from nu.inspect import BuilderRecord, RefRecord, parse_ref, verify_ref
from nu.mem.refs.items import IntRef, ItemRef, StrRef


def test_a_ref_is_a_builder_record_dispatch_tagged() -> None:
    record = parse_ref(IntRef)
    assert isinstance(record, RefRecord)
    assert isinstance(record, BuilderRecord)
    assert record.name == "IntRef"


def test_typed_refs_carry_the_form_operator_surface() -> None:
    spellings = {m.spelling for m in parse_ref(IntRef).methods}
    assert "a + b" in spellings
    assert ".set(...)" in spellings
    assert ".inc(...)" in spellings


def test_untyped_ref_carries_only_the_ref_surface() -> None:
    spellings = {m.spelling for m in parse_ref(ItemRef).methods}
    assert ".set(...)" in spellings
    assert "a + b" not in spellings


def test_str_ref_parses() -> None:
    assert parse_ref(StrRef).name == "StrRef"


def test_a_ref_answers_the_same_taxonomy_questions_an_atom_does() -> None:
    record = parse_ref(IntRef)
    assert (record.kind, record.sort, record.cardinality) == ("Ref", "ref", "scalar")
    assert record.abstract is False


def test_a_ref_knows_the_module_it_is_defined_in() -> None:
    record = parse_ref(IntRef, path="nu.mem.IntRef")
    assert record.path == "nu.mem.IntRef"
    assert record.module == "nu.mem.refs.items"


def test_ref_docstrings_are_clean_by_the_shared_laws() -> None:
    assert verify_ref(IntRef) == []
    assert verify_ref(ItemRef) == []
