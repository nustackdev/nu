"""Value constructors build values on the forms and are absent on every ref class."""

from __future__ import annotations

import pytest

import nu
from nu.mem import DictRef, ListRef, SetRef


@pytest.mark.parametrize(
    ("form", "empty"),
    [(nu.Dict, {}), (nu.List, []), (nu.Set, set()), (nu.FrozenSet, frozenset()), (nu.Tuple, ())],
)
def test_forms_build_values(form, empty):
    assert nu.run(form.create())[0] == empty


def test_a_form_subclass_keeps_its_constructors():
    class Pairs(nu.Dict):
        pass

    assert nu.run(Pairs.of(a=1))[0] == {"a": 1}


@pytest.mark.parametrize("ref", [DictRef, ListRef, SetRef])
@pytest.mark.parametrize("name", ["of", "create"])
def test_ref_classes_have_no_value_constructor(ref, name):
    assert not hasattr(ref, name)
    with pytest.raises(AttributeError, match="a ref names a place"):
        getattr(ref, name)
