"""Wire envelope: a Frame's ``ref`` is a path, and it stays one.

The address a Ref resolves to is a tuple of segments, so the wire carries
a list. Nothing joins it: a segment may hold any character, dots included,
and joining would let two different paths land on the same browser slice.
"""

from __future__ import annotations

from nustd.ui.core.protocol import OP_WRITE, Frame, decode, encode


def test_frame_ref_defaults_to_the_empty_path():
    frame = Frame(OP_WRITE, payload={"name": "App"})
    assert frame.ref == ()
    assert frame.to_dict()["ref"] == []


def test_frame_ref_round_trips_as_a_list():
    frame = Frame("write", ref=("HomePage", "panel", "label"), payload="hi")
    back = decode(encode(frame))
    assert back.ref == ("HomePage", "panel", "label")
    assert back.op == "write"
    assert back.payload == "hi"


def test_a_segment_may_contain_dots():
    """Two paths that would collide under a dot join stay distinct."""
    one = decode(encode(Frame("write", ref=("ops.page.create",), payload=1)))
    two = decode(encode(Frame("write", ref=("ops", "page", "create"), payload=2)))
    assert one.ref != two.ref


def test_a_frame_without_a_chain_is_what_it_always_was():
    """The field is additive: no chain, no key, same bytes as before."""
    frame = Frame("write", ref=("home", "label"), payload="hi")
    assert frame.chain == ()
    assert frame.to_dict() == {"op": "write", "ref": ["home", "label"], "payload": "hi"}
    assert decode(encode(frame)).chain == ()


def test_chain_round_trips_as_segment_type_props_triples():
    """Root-first triples, dots and all -- the chain is a sequence for the
    same reason the path is."""
    chain = (
        ("ops.page.create", "Card", {"title": "Ops"}),
        ("label", "TextRef", {}),
    )
    back = decode(encode(Frame("write", ref=("ops.page.create", "label"), chain=chain)))
    assert back.chain == chain
    assert back.ref == ("ops.page.create", "label")
