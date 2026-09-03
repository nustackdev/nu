"""Tests for nu.info.interactions - the Inspect atom."""

from __future__ import annotations

import nu
from nu.info.interactions import render


def test_module_render_has_forms_refs_interactions_when_present() -> None:
    text = render("nu.core.arithmetic")
    assert text.startswith("MODULE  nu.core.arithmetic")
    assert "INTERACTIONS" in text
    assert "Add" in text
    assert "Sub" in text


def test_atom_render_dispatches_to_form_for_a_form_subclass() -> None:
    text = render("nu.forms.primitives.Int")
    assert text.startswith("FORM  nu.forms.primitives.Int")
    assert "methods (" in text
    assert "a + b" in text


def test_atom_render_dispatches_to_ref_for_a_ref_subclass() -> None:
    text = render("nu.mem.refs.items.IntRef")
    assert text.startswith("REF  nu.mem.refs.items.IntRef")
    assert ".inc(" in text


def test_atom_render_dispatches_to_interaction_for_a_bare_interaction() -> None:
    text = render("nu.core.arithmetic.Add")
    assert text.startswith("INTERACTION  nu.core.arithmetic.Add")
    assert "yields" in text
    assert "examples" in text


def test_unknown_path_yields_empty_string() -> None:
    assert render("nu.does.not.exist.At.All") == ""


def test_inspect_atom_runs_end_to_end() -> None:
    text = nu.run(nu.info.Inspect("nu.core.arithmetic.Add"))[0]
    assert isinstance(text, str)
    assert "INTERACTION" in text


def test_inspect_yields_invalid_on_unknown_path() -> None:
    from nu.lang.sentinels import INVALID

    assert nu.run(nu.info.Inspect("nowhere.at.all"))[0] is INVALID
