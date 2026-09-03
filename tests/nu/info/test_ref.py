"""Tests for nu.info.ref - RefRecord over BuilderRecord."""

from __future__ import annotations

from nu.info import BuilderRecord, RefRecord, parse_ref, verify_ref
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


def test_ref_docstrings_are_clean_by_the_shared_laws() -> None:
    assert verify_ref(IntRef) == []
    assert verify_ref(ItemRef) == []
