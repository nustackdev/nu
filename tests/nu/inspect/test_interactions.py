"""Tests for nu.inspect.interactions - the Inspect atom."""

from __future__ import annotations

import nu
from nu.inspect.interactions import render


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
    text = nu.run(nu.inspect.Inspect("nu.core.arithmetic.Add"))[0]
    assert isinstance(text, str)
    assert "INTERACTION" in text


def test_inspect_yields_invalid_on_unknown_path() -> None:
    from nu.lang.sentinels import INVALID

    assert nu.run(nu.inspect.Inspect("nowhere.at.all"))[0] is INVALID


# --- the declarative kinds: a user's own app -------------------------------


def test_module_render_lists_the_shapes_and_services_an_app_declares() -> None:
    text = render("_support.app")
    assert text.startswith("MODULE  _support.app")
    assert "SHAPES (2)" in text
    assert "SERVICES (1)" in text


def test_shape_render_is_prose_plus_one_line_per_slot() -> None:
    text = render("_support.app.Task")
    assert text.startswith("SHAPE  _support.app.Task")
    assert "entries (3)" in text
    assert "owner" in text
    # Two levels, not a tree: the nested shape's own slots are not in here.
    assert "email" not in text


def test_a_shape_of_three_slots_renders_in_a_dozen_lines() -> None:
    assert len(render("_support.app.Task").splitlines()) < 16


def test_slot_render_resolves_through_the_shape_to_the_ref() -> None:
    text = render("_support.app.Task.title")
    assert text.startswith("REF  _support.app.Task.title  (StrRef)")
    assert ".set(...)" in text


def test_a_nested_shape_slot_renders_as_a_shape_and_can_be_walked_through() -> None:
    assert render("_support.app.Task.owner").startswith("SHAPE  _support.app.Task.owner")
    assert render("_support.app.Task.owner.email").startswith("REF  _support.app.Task.owner.email")


def test_service_and_method_render() -> None:
    text = render("_support.app.GH")
    assert text.startswith("SERVICE  _support.app.GH")
    assert "get_repo" in text
    assert "/repos/{owner}/{name}" in text
    assert render("_support.app.GH.get_repo").startswith("REF  _support.app.GH.get_repo  (GETRef)")


def test_a_name_the_shape_does_not_declare_is_a_miss() -> None:
    assert render("_support.app.Task.nope") == ""
    assert render("_support.app.Task.title.nope") == ""


def test_inspect_atom_reads_a_user_shape_end_to_end() -> None:
    text = nu.run(nu.inspect.Inspect("_support.app.Task"))[0]
    assert isinstance(text, str)
    assert "SHAPE" in text
