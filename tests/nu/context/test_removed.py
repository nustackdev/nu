"""The context holds frames only: the attrs name store and its surface are gone."""

from __future__ import annotations

import pytest

import nu
import nu.lang.runtime


@pytest.mark.parametrize("name", ["Let", "TupleRef", "FrozenSetRef", "Attr", "AttrExists", "Frame"])
def test_the_removed_names_are_not_on_nu(name):
    assert not hasattr(nu, name)


@pytest.mark.parametrize("name", ["Attr", "AttrExists", "attrs"])
def test_the_removed_names_are_not_on_nu_context(name):
    assert not hasattr(nu.context, name)


def test_the_name_store_is_gone_from_the_runtime():
    assert not hasattr(nu.lang.runtime, "Attributes")
    assert not hasattr(nu.Context(), "attrs")
    assert not hasattr(nu.Context(), "branch")


def test_a_context_takes_no_seed_names():
    with pytest.raises(TypeError):
        nu.Context(attrs={"x": 1})  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "name", ["IntRef", "StrRef", "FloatRef", "BoolRef", "BytesRef", "ObjectRef"]
)
def test_the_typed_ref_names_on_nu_are_the_mem_refs(name):
    assert getattr(nu, name) is getattr(nu.mem, name)
