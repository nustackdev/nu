"""auto_flow_atomic: Eval branches are opaque and left unwrapped.

A Eval subtree's effect surface is not visible at compile time. The
flow-based bottom-up wrapper skips any branch whose effective root
(through Spans) is a Eval: no Snapshot / Transaction wraps around it.
Non-Eval siblings are still wrapped normally.
"""

from __future__ import annotations

from _support.dyn_carriers import ConstCarrier
from _support.law_terms import Q

from nu.core.flows import Sequential as Seq
from nu.domains.shape import Shape
from nu.kv import (
    IntRef,
    Snapshot,
    Transaction,
    auto_flow_atomic,
)
from nu.lang import Bracket
from nu.prog import Eval


class Account(Shape):
    balance = IntRef.slot()


def _write_cmd(ref):
    return ref.set(0)


def _collect(tree, cls):
    out = []
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, cls):
            out.append(node)
        if node._children:
            stack.extend(reversed(node._children))
    return out


def test_dyn_branch_is_not_wrapped() -> None:
    ref = Account.balance
    tree = Seq(_write_cmd(ref), Eval(ConstCarrier(Q())))

    out = auto_flow_atomic(tree)

    # The Cmd branch is wrapped; the Eval branch is untouched.
    assert len(_collect(out, Transaction)) == 1
    assert isinstance(out._children[1], Eval)


def test_bracket_over_dyn_is_still_skipped_via_span_lookthrough() -> None:
    ref = Account.balance
    tree = Seq(_write_cmd(ref), Bracket(Eval(ConstCarrier(Q()))))

    out = auto_flow_atomic(tree)

    # The Cmd branch is wrapped; the Bracket-wrapped-Eval branch is untouched.
    assert len(_collect(out, Transaction)) == 1
    assert isinstance(out._children[1], Bracket)
    assert isinstance(out._children[1]._children[0], Eval)
    assert len(_collect(out, Snapshot)) == 0


def test_iter_uncovered_stops_at_dyn_boundary() -> None:
    """Eval opacity: _iter_uncovered must not descend into a Eval carrier.

    Refs sitting inside the carrier subtree are hidden from the wrap
    decision. Sibling branches still see their own refs normally.
    """
    from nu.kv.tree.auto_flow_atomic import _iter_uncovered

    ref = Account.balance
    # Bracket(ref) puts the ref in _children so a naive descent would find
    # it. Wrapped in Eval, the walker must stop at the Eval boundary.
    dyn_branch = Eval(Bracket(ref))
    sibling = _write_cmd(ref)
    tree = Seq(dyn_branch, sibling)

    # Direct check: Eval is opaque, no refs leak out.
    assert list(_iter_uncovered(dyn_branch, None, ())) == []

    # Sibling still visible; wrap decision fires only on the sibling branch.
    out = auto_flow_atomic(tree)
    assert isinstance(out._children[0], Eval)
    assert len(_collect(out, Transaction)) == 1


def test_dyn_inside_inner_sequential_does_not_block_outer_wrap() -> None:
    ref = Account.balance
    inner = Seq(_write_cmd(ref), Eval(ConstCarrier(Q())))
    tree = Seq(_write_cmd(ref), inner)

    out = auto_flow_atomic(tree)

    # Outer Cmd gets wrapped. The inner Flow child is left as-is at outer
    # level (Flow-child rule), but its own Cmd gets wrapped by the recursive
    # walk. The inner Eval branch stays untouched.
    txns = _collect(out, Transaction)
    assert len(txns) == 2
