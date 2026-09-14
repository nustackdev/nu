"""Boot batch resolution: which shape owns the addresses in a tree.

`_resolve_boot` reads the Nu tree, finds the shape every UI Ref is rooted
on, and returns the chains the browser builds its tree from. The rule under
test is that a page's leading segment comes from the Index slot it was
reached through -- so the chains that go out at boot and the addresses the
Refs resolve to are the same tuples.
"""

from __future__ import annotations

import pytest

from nu.ui.nudle import Index, Page
from nu.ui.nudle.serve import _resolve_boot
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


def _paths(chains):
    return [tuple(seg for seg, _, _ in chain) for chain in chains]


def test_index_chains_match_the_ref_chain():
    name, chains, sidebar = _resolve_boot(MountApp.shown.panel.label.set("x"))
    assert name == "MountApp"
    assert _paths(chains) == [
        ("title",),
        ("shown",),
        ("shown", "panel"),
        ("shown", "panel", "label"),
        ("other",),
        ("other", "panel"),
        ("other", "panel", "label"),
    ]
    assert sidebar is True


def test_a_page_node_carries_its_route_and_label():
    _, chains, _ = _resolve_boot(MountApp.shown.panel.label.set("x"))
    pages = {chain[-1][0]: chain[-1][2] for chain in chains if chain[-1][1] == "Page"}
    assert pages == {
        "shown": {"route": "/", "label": "home"},
        "other": {"route": "/other", "label": "other"},
    }


def test_a_section_reports_the_type_the_browser_knows():
    _, chains, _ = _resolve_boot(MountApp.shown.panel.label.set("x"))
    types = {chain[-1][0]: chain[-1][1] for chain in chains}
    # Panel is a user subclass of Row; Row is the name the registry has.
    assert types["panel"] == "Row"
    assert types["label"] == "TextRef"


def test_page_no_index_declares_boots_bare():
    class Loose(Page):
        panel = Panel.slot()

    name, chains, sidebar = _resolve_boot(Loose.panel.label.set("x"))
    assert name == "Loose"
    assert _paths(chains) == [("panel",), ("panel", "label")]
    assert sidebar is False


def test_class_handle_for_a_declared_page_is_refused():
    with pytest.raises(RuntimeError, match=r"MountApp\.shown"):
        _resolve_boot(Shown.panel.label.set("x"))


def test_section_class_handle_is_refused():
    with pytest.raises(RuntimeError, match="no mount point"):
        _resolve_boot(Panel.label.set("x"))
