"""Mount payload resolution: which shape owns the addresses in a tree.

`_resolve_mount` reads the Nu tree, finds the shape every UI Ref is rooted
on, and returns the payload the browser mounts from. The rule under test is
that a page's leading segment comes from the Index slot it was reached
through -- so the fields the browser mounts and the addresses the Refs
resolve to are the same tuples.
"""

from __future__ import annotations

import pytest

from nu.ui.nudle import Index, Page
from nu.ui.nudle.serve import _resolve_mount
from nu.ui.refs import Row, TextRef


class Panel(Row):
    label = TextRef.slot()


class Shown(Page):
    panel = Panel.slot()


class Hidden(Page):
    panel = Panel.slot()


class MountApp(Index):
    title = TextRef.slot()
    shown = Shown.slot("/")
    other = Hidden.slot("/other")


def test_index_payload_paths_match_the_ref_chain():
    name, structural, pages, sidebar = _resolve_mount(MountApp.shown.panel.label.set("x"))
    assert name == "MountApp"
    assert [f["path"] for f in structural] == [("title",)]
    assert [(p["route"], p["name"]) for p in pages] == [("/", "shown"), ("/other", "other")]
    shown_fields = pages[0]["fields"]
    assert shown_fields[0]["path"] == ("shown", "panel")
    assert shown_fields[0]["fields"][0]["path"] == ("shown", "panel", "label")
    assert sidebar is True


def test_page_no_index_declares_is_auto_mounted_bare():
    class Loose(Page):
        panel = Panel.slot()

    name, structural, pages, sidebar = _resolve_mount(Loose.panel.label.set("x"))
    assert name == "_AutoIndex"
    assert structural == []
    assert pages[0]["route"] == "/"
    assert pages[0]["fields"][0]["path"] == ("panel",)
    assert sidebar is False


def test_class_handle_for_a_declared_page_is_refused():
    with pytest.raises(RuntimeError, match=r"MountApp\.shown"):
        _resolve_mount(Shown.panel.label.set("x"))


def test_section_class_handle_is_refused():
    with pytest.raises(RuntimeError, match="no mount point"):
        _resolve_mount(Panel.label.set("x"))
