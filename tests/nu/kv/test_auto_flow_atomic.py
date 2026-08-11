"""Tests for auto_flow_atomic deformation.

Focus: structural invariants of the flow-based wrapping pass (which
boundaries land where) without requiring live storage/navigator setup.
Checks:

- Scoped pass only wraps Flow children whose subtree has an uncovered
  WRITE through a virtuals ref matching that scope.
- Unscoped pass wraps every Flow child not already covered.
- Applying scoped(X) then unscoped produces a tree with the same
  coverage as unscoped then scoped(X) — order-independence. No redundant
  nested boundaries.
- A WRITE nested under a Transaction with compatible scope is not
  re-wrapped (skip-already-covered).
"""

from __future__ import annotations

from nu.domains.shape import Shape
from nu.flows import Sequential as Seq
from nu.kv import (
    IntRef,
    Snapshot,
    StrRef,
    Transaction,
    auto_flow_atomic,
)


def _write_cmd(ref):
    """A stand-in write Command for tests -- any Command with ``_mutates``
    that wraps ``ref`` at ``_children[0]`` works for the flow-wrapping
    passes under test. ``.set(0)`` compiles to a ``SetCmd`` whose
    first child is the ref, which is what the deformer keys on."""
    return ref.set(0)


def _flat_ref(root_shape: type):
    """A real virtuals leaf ref rooted at the given shape (structural stand-in).

    The wrapping pass only cares that this is a virtuals ref whose root shape
    is ``root_shape``; any leaf slot on the shape works.
    """
    return root_shape.height if root_shape is LedgerShard else root_shape.balance


# =============================================================================
# SHAPES
# =============================================================================


class LedgerShard(Shape):
    height = IntRef.slot()
    name = StrRef.slot()


class Account(Shape):
    balance = IntRef.slot()


# =============================================================================
# HELPERS
# =============================================================================


def _count(tree, cls, scope_sentinel=object()) -> int:  # noqa: B008
    """Count ContextManager boundaries of ``cls`` in the tree.

    If scope_sentinel is given, only count ones with ``.scope is scope_sentinel``.
    """
    n = 0
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, cls):
            if scope_sentinel is _count.__defaults__[0]:
                n += 1
            elif node.scope is scope_sentinel:
                n += 1
        if node._children:
            stack.extend(node._children)
    return n


def _collect(tree, cls):
    """Return all nodes of type ``cls`` in the tree (pre-order)."""
    out = []
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, cls):
            out.append(node)
        if node._children:
            # reverse to keep pre-order-ish
            stack.extend(reversed(node._children))
    return out


def _structure(tree) -> str:
    """Render a compact textual signature of the boundary structure.

    Only shows Transaction/Snapshot nodes and their nesting, ignoring other
    ops. Good enough for order-independence comparisons.
    """
    if isinstance(tree, (Transaction, Snapshot)):
        scope_name = tree.scope.__name__ if hasattr(tree.scope, "__name__") else repr(tree.scope)
        cls_name = type(tree).__name__
        inner = ",".join(_structure(c) for c in tree._children if not isinstance(c, type(None)))
        return f"{cls_name}({scope_name}){{{inner}}}"
    if not tree._children:
        return ""
    parts = [_structure(c) for c in tree._children]
    parts = [p for p in parts if p]
    return ",".join(parts)


# =============================================================================
# TESTS
# =============================================================================


def test_scoped_wraps_only_matching_writes() -> None:
    shard_ref = _flat_ref(LedgerShard)
    acct_ref = _flat_ref(Account)
    tree = Seq(
        _write_cmd(shard_ref),
        _write_cmd(acct_ref),
    )

    out = auto_flow_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    # exactly one Transaction, around the shard-targeted cmd
    assert len(txns) == 1
    assert txns[0].scope is LedgerShard


def test_unscoped_wraps_everything() -> None:
    shard_ref = _flat_ref(LedgerShard)
    acct_ref = _flat_ref(Account)
    tree = Seq(
        _write_cmd(shard_ref),
        _write_cmd(acct_ref),
    )

    out = auto_flow_atomic(tree)

    txns = _collect(out, Transaction)
    assert len(txns) == 2
    assert all(t.scope is None for t in txns)


def test_scoped_then_unscoped_no_double_wrap() -> None:
    """Regression: unscoped pass after scoped pass must not re-wrap.

    A bare cmd is not a Flow child on its own — the outer tree here is the
    cmd itself. Neither pass finds a Flow at the root, so both are no-ops.
    """
    shard_ref = _flat_ref(LedgerShard)
    tree = Seq(_write_cmd(shard_ref))

    t1 = auto_flow_atomic(tree, scope=LedgerShard)
    t2 = auto_flow_atomic(t1)

    txns = _collect(t2, Transaction)
    assert len(txns) == 1
    assert txns[0].scope is LedgerShard


def test_unscoped_then_scoped_no_double_wrap() -> None:
    """Reverse order: scoped pass after unscoped must not re-wrap either."""
    shard_ref = _flat_ref(LedgerShard)
    tree = Seq(_write_cmd(shard_ref))

    t1 = auto_flow_atomic(tree)
    t2 = auto_flow_atomic(t1, scope=LedgerShard)

    txns = _collect(t2, Transaction)
    assert len(txns) == 1
    # unscoped pass ran first, so scope is None and covers everything
    assert txns[0].scope is None


def test_order_independence_mixed_scopes() -> None:
    """Tree with writes at two scopes — applying both passes in either order
    yields the same set of *covering* boundaries (one Transaction per write),
    and never nests Transactions.

    Exact scope tags may differ between orders (whichever pass ran first
    claims each write), but each write must end up with a single covering
    Transaction and no Transaction-inside-Transaction."""
    shard_ref = _flat_ref(LedgerShard)
    acct_ref = _flat_ref(Account)
    tree = Seq(
        _write_cmd(shard_ref),
        _write_cmd(acct_ref),
    )

    a = auto_flow_atomic(auto_flow_atomic(tree, scope=LedgerShard))
    b = auto_flow_atomic(auto_flow_atomic(tree), scope=LedgerShard)

    # Each order: exactly two Transactions (one per write), none nested.
    for label, t in (("a", a), ("b", b)):
        txns = _collect(t, Transaction)
        assert len(txns) == 2, f"{label}: expected 2 Transactions, got {len(txns)}"
        # no Transaction contains another Transaction
        for txn in txns:
            inner_txns = [n for n in _collect(txn, Transaction) if n is not txn]
            assert not inner_txns, f"{label}: nested Transaction: {inner_txns}"


def test_preexisting_transaction_covers_nested_write() -> None:
    """Manually-placed Transaction must prevent inner re-wrapping."""
    shard_ref = _flat_ref(LedgerShard)
    tree = Seq(Transaction(_write_cmd(shard_ref), scope=LedgerShard))

    out = auto_flow_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    assert len(txns) == 1
    assert out is tree  # no rewrite needed


def test_unscoped_boundary_covers_scoped_pass() -> None:
    """Transaction(scope=None) already covers any ref — scoped pass must skip."""
    shard_ref = _flat_ref(LedgerShard)
    tree = Seq(Transaction(_write_cmd(shard_ref), scope=None))

    out = auto_flow_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    assert len(txns) == 1
    assert txns[0].scope is None


def test_bracket_over_bare_ref_with_mismatched_scope_gets_external_wrapped() -> None:
    """A user-written ``Snapshot(bare_ref)`` whose scope does not cover the
    ref's own shape must trigger an outer wrap under the covering scope.

    Regression: an earlier iteration of ``_iter_uncovered`` only inspected
    ``node._children`` and missed the case where the walked subtree IS a
    virtuals Ref, so a bare-Ref-body inside a mismatched-scope bracket
    silently escaped external-wrapping.
    """
    shard_ref = _flat_ref(LedgerShard)
    # Snapshot claims Account scope but its body is a LedgerShard ref —
    # nothing covers the ref, so the outer Seq's Flow-child rule must add
    # a LedgerShard-covering wrap around the whole bracket.
    tree = Seq(Snapshot(shard_ref, scope=Account))

    out = auto_flow_atomic(tree, scope=LedgerShard)

    snaps = _collect(out, Snapshot)
    # two Snapshots: the original (Account) and the outer wrap (LedgerShard).
    assert len(snaps) == 2
    scopes = {s.scope for s in snaps}
    assert scopes == {Account, LedgerShard}


def test_bracket_over_bare_ref_matching_scope_left_alone() -> None:
    """A user-written ``Snapshot(bare_ref, scope=S)`` where S matches the
    ref's shape is fully covered and must not be re-wrapped."""
    shard_ref = _flat_ref(LedgerShard)
    tree = Seq(Snapshot(shard_ref, scope=LedgerShard))

    out = auto_flow_atomic(tree, scope=LedgerShard)

    snaps = _collect(out, Snapshot)
    assert len(snaps) == 1
    assert snaps[0].scope is LedgerShard
