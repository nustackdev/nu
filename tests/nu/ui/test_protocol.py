"""Wire envelope: a Frame's ``ref`` is a path, and it stays one.

The address a Ref resolves to is a tuple of segments, so the wire carries
a list. Nothing joins it: a segment may hold any character, dots included,
and joining would let two different paths land on the same browser slice.
"""

from __future__ import annotations

from nu.ui.core.protocol import OP_MOUNT, Frame, decode, encode


def test_frame_ref_defaults_to_the_empty_path():
    frame = Frame(OP_MOUNT, payload={"name": "App"})
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
