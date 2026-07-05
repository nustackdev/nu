"""Tier tests for CollectionForm.extract() — available on immutable base tier.

Uses the concrete Ref types (MappingRef, SequenceRef, SetRef) which inherit
CollectionForm, to verify that extract() is wired up and returns an
ExtractQuery on all three collection families.
"""

from __future__ import annotations

from nu.domains.shape.interactions import ExtractQuery
from nu.domains.shape.refs.mapping import MappingRef
from nu.domains.shape.refs.sequence import SequenceRef
from nu.domains.shape.refs.set_ import SetRef


def test_mapping_ref_extract_returns_extract_query():
    ref = MappingRef("data")
    result = ref.extract()
    assert isinstance(result, ExtractQuery)


def test_sequence_ref_extract_returns_extract_query():
    ref = SequenceRef("items")
    result = ref.extract()
    assert isinstance(result, ExtractQuery)


def test_set_ref_extract_returns_extract_query():
    ref = SetRef("tags")
    result = ref.extract()
    assert isinstance(result, ExtractQuery)


def test_extract_query_wraps_ref():
    ref = MappingRef("data")
    result = ref.extract()
    assert result._children[0] is ref
