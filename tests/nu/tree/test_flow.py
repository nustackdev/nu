"""Tests for nu.tree: flow-aware wrapping primitives.

is_flow, touches_fabric, has_write_on_fabric, wrap_flows, wrap_flow_children.
All tests work on the Nu-layer tree with no substrate needed.
"""

from __future__ import annotations

from nu.core import Literal
from nu.domains.shape.interactions import Load
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.mapping import MappingRef
from nu.engine.structure import Declared
from nu.lang import Control
from nu.tree import (
    has_write_on_fabric,
    is_flow,
    touches_fabric,
    wrap_flow_children,
    wrap_flows,
)


# ---------------------------------------------------------------------------
# Minimal concrete Flow for testing (Control subclass)
# ---------------------------------------------------------------------------


class SimpleFlow(Control):
    """Minimal Flow with a body child."""

    _mutates = Declared(value=frozenset(), name="mutates")


# ---------------------------------------------------------------------------
# is_flow
# ---------------------------------------------------------------------------


def test_is_flow_true_for_flow_instance():
    flow = SimpleFlow(Literal(1))
    assert is_flow(flow) is True


def test_is_flow_false_for_non_flow():
    q = Literal(42)
    assert is_flow(q) is False


def test_is_flow_false_for_ref():
    ref = ItemRef("x")
    assert is_flow(ref) is False


# ---------------------------------------------------------------------------
# touches_fabric
# ---------------------------------------------------------------------------


def test_touches_fabric_true_when_ref_type_present():
    q = Load(ItemRef("slot"))
    assert touches_fabric(q, (ItemRef,)) is True


def test_touches_fabric_false_when_ref_type_absent():
    q = Load(ItemRef("slot"))
    assert touches_fabric(q, (MappingRef,)) is False


def test_touches_fabric_false_for_pure_literal():
    q = Literal(5)
    assert touches_fabric(q, (ItemRef,)) is False


# ---------------------------------------------------------------------------
# has_write_on_fabric
# ---------------------------------------------------------------------------


def test_has_write_on_fabric_false_for_read_only_query():
    # Load has no mutates; ItemRef slot binds as READ
    q = Load(ItemRef("slot"))
    assert has_write_on_fabric(q, (ItemRef,)) is False


# ---------------------------------------------------------------------------
# wrap_flows
# ---------------------------------------------------------------------------


def _tag(node):
    """Wrap a node in a Literal to mark it was visited."""
    # We use with_children to produce a structural variant; we track by identity.
    return node._with_children(*node._children)


def test_wrap_flows_calls_wrapper_on_outermost_flow():
    called = []

    def wrapper(f):
        called.append(f)
        return f

    flow = SimpleFlow(Literal(1))
    wrap_flows(flow, wrapper)
    assert len(called) == 1
    assert called[0] is flow


def test_wrap_flows_does_not_recurse_inside_wrapped_flow():
    called = []

    def wrapper(f):
        called.append(f)
        return f

    inner = SimpleFlow(Literal(0))
    outer = SimpleFlow(inner)
    wrap_flows(outer, wrapper)
    # Only outer should be wrapped; inner is inside the claimed subtree
    assert len(called) == 1
    assert called[0] is outer


def test_wrap_flows_with_predicate_skips_non_matching():
    called = []

    def wrapper(f):
        called.append(f)
        return f

    flow = SimpleFlow(Literal(1))
    wrap_flows(flow, wrapper, predicate=lambda _: False)
    assert called == []


def test_wrap_flows_returns_unchanged_tree_for_pure_query():
    q = Load(ItemRef("x"))
    result = wrap_flows(q, lambda n: n)
    assert result is q


# ---------------------------------------------------------------------------
# wrap_flow_children
# ---------------------------------------------------------------------------


def test_wrap_flow_children_wraps_direct_children():
    wrapped = []

    def wrapper(child):
        wrapped.append(child)
        return child

    body = Literal(7)
    flow = SimpleFlow(body)
    wrap_flow_children(flow, wrapper)
    assert len(wrapped) == 1
    assert wrapped[0] is body
