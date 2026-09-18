"""Tests for nu.shape.rewrite: re-rooting bare ref chains under a new parent.

Pure structural -- blueprint refs, never compiled. Covers the splice itself,
the exemption predicate, the payload copy, root_shape, recursion into every
child (addresses and Eval carriers included), and identity preservation.
"""

from __future__ import annotations

from nu.core.flows import Sequential
from nu.domains.shape import Shape, reroot, rerooter
from nu.domains.shape.refs.base import ANCHOR, StructuredRef
from nu.domains.shape.refs.item import MutableItemRef
from nu.lang import Literal
from nu.prog import Eval


class Host(Shape):
    pass


class Block(Shape):
    pass


def ref(address, parent=None, owner=Block):
    return MutableItemRef(address, parent_ref=parent, owner_shape=owner)


def path(node):
    """Static addresses of a chain, root-first."""
    segs = []
    while isinstance(node, StructuredRef):
        segs.append(node._children[1])
        node = node._children[0]
    segs.reverse()
    return tuple(s._payload["value"] if isinstance(s, Literal) else s for s in segs)


def chain_root(node):
    while isinstance(node._children[0], StructuredRef):
        node = node._children[0]
    return node


def the_ref(node):
    """The first ref reachable from a rewritten command tree."""
    if isinstance(node, StructuredRef):
        return node
    for child in node._children:
        found = the_ref(child)
        if found is not None:
            return found
    return None


def under():
    return ref("sections", parent=ref("page", owner=Host), owner=Host)


# --- the splice -----------------------------------------------------------


def test_a_bare_chain_lands_under_the_new_parent():
    out = reroot(ref("inp", parent=ref("form")), under())
    assert path(out) == ("page", "sections", "form", "inp")


def test_the_source_chain_is_untouched():
    source = ref("inp", parent=ref("form"))
    reroot(source, under())
    assert path(source) == ("form", "inp")


def test_the_source_payload_is_not_aliased():
    source = ref("inp")
    reroot(source, under())
    assert source._payload["root_shape"] is Block


def test_a_ref_buried_under_a_flow_is_reached():
    out = reroot(Sequential(Literal(1), ref("inp")), under())
    assert path(the_ref(out)) == ("page", "sections", "inp")


def test_a_ref_under_a_command_is_reached():
    out = reroot(ref("inp").set("hi"), under())
    assert path(the_ref(out)) == ("page", "sections", "inp")


def test_a_ref_in_an_eval_carrier_is_reached():
    out = reroot(Eval(ref("inp")), under())
    assert path(the_ref(out)) == ("page", "sections", "inp")


# --- root_shape -----------------------------------------------------------


def test_the_spliced_chain_takes_the_parents_root_shape():
    out = reroot(ref("inp", parent=ref("form")), under())
    assert out._root_shape is Host
    assert out._children[0]._root_shape is Host


def test_an_exempt_chain_keeps_its_own_root_shape():
    out = reroot(ref("inp", parent=ref("form")), under(), rooted=lambda _: True)
    assert out._root_shape is Block


# --- the exemption --------------------------------------------------------


def test_a_claimed_chain_root_is_left_alone():
    out = reroot(ref("inp", parent=ref("form")), under(), rooted=lambda _: True)
    assert path(out) == ("form", "inp")
    assert chain_root(out)._children[0] is ANCHOR


def test_the_predicate_sees_the_chain_root_not_the_leaf():
    seen = []
    reroot(ref("inp", parent=ref("form")), under(), rooted=lambda r: seen.append(r) or False)
    assert [path(r) for r in seen] == [("form",)]


def test_only_the_claimed_chains_are_left_alone():
    mine = ref("form")
    theirs = ref("other")
    out = reroot(
        Sequential(ref("inp", parent=mine), ref("tick", parent=theirs)),
        under(),
        rooted=lambda r: r._children[1]._payload["value"] == "other",
    )
    kept, spliced = out._children[1], out._children[0]
    assert path(spliced) == ("page", "sections", "form", "inp")
    assert path(kept) == ("other", "tick")


# --- addresses are children too -------------------------------------------


def test_a_dynamic_address_that_is_a_ref_moves_too():
    out = reroot(ref(ref("cursor")), under())
    assert path(out._children[1]) == ("page", "sections", "cursor")


def test_an_address_inside_an_exempt_chain_is_still_judged_on_its_own():
    out = reroot(
        ref(ref("cursor"), parent=ref("form")),
        under(),
        rooted=lambda r: r._children[1]._payload["value"] == "form",
    )
    # the spine was claimed, the address is its own chain and was not
    assert path(out._children[0]) == ("form",)
    assert path(out._children[1]) == ("page", "sections", "cursor")


# --- identity -------------------------------------------------------------


def test_an_untouched_tree_comes_back_as_itself():
    source = Sequential(Literal(1), ref("inp"))
    assert reroot(source, under(), rooted=lambda _: True) is source


def test_a_tree_with_no_refs_comes_back_as_itself():
    source = Sequential(Literal(1), Literal(2))
    assert reroot(source, under()) is source


# --- rerooter -------------------------------------------------------------


def test_rerooter_is_reroot_with_its_policy_bound():
    transform = rerooter(under())
    assert path(transform(ref("inp"))) == ("page", "sections", "inp")


def test_rerooter_carries_the_predicate():
    transform = rerooter(under(), rooted=lambda _: True)
    assert path(transform(ref("inp"))) == ("inp",)
