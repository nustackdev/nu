"""A kv ref class names a place, so it has none of the value forms' constructors."""

from __future__ import annotations

import pytest

from nustd.kv import (
    DictRef,
    ListRef,
    LogDictRef,
    OrderedDictRef,
    PrimitiveDictRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    SetRef,
)


@pytest.mark.parametrize(
    "ref",
    [
        DictRef,
        OrderedDictRef,
        LogDictRef,
        ListRef,
        SetRef,
        PrimitiveDictRef,
        PrimitiveListRef,
        PrimitiveSetRef,
    ],
)
@pytest.mark.parametrize("name", ["of", "create"])
def test_kv_ref_classes_have_no_value_constructor(ref, name):
    assert not hasattr(ref, name)
