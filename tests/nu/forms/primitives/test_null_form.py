"""NullForm: the form of the NULL value, and the term a branch yields NULL with."""

from __future__ import annotations

import pytest

import nu
from nu.lang import is_null


def test_create_builds_a_null_form() -> None:
    term = nu.NullForm.create()
    assert isinstance(term, nu.NullForm)
    assert is_null(nu.run(term)[0])


def test_a_branch_yields_null_through_create() -> None:
    found = nu.If(False, nu.Int(1), nu.NullForm.create())
    assert is_null(nu.run(found)[0])
    assert nu.run(nu.Int(found).fallback(7))[0] == 7
    assert nu.run(nu.Int(nu.If(True, nu.Int(1), nu.NullForm.create())).fallback(7))[0] == 1


def test_a_null_branch_reads_null_in_is_null() -> None:
    assert nu.run(nu.IsNull(nu.NullForm.create()))[0] is True


def test_create_takes_no_arguments() -> None:
    with pytest.raises(TypeError):
        nu.NullForm.create(1)  # type: ignore[call-arg]
