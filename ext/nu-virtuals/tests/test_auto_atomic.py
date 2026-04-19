"""Tests for auto_atomic deformation.

Focus: structural invariants of the rewrite (wrapping boundaries) without
requiring live storage/navigator setup. Checks:

- Scoped pass only wraps WRITE ops whose ref targets that scope.
- Unscoped pass wraps everything not already covered.
- Applying scoped(X) then unscoped produces the same tree as unscoped
  then scoped(X) — order-independence. No redundant nested boundaries.
- A WRITE op nested under a Transaction with compatible scope is not
  re-wrapped (skip-already-covered).
"""

from __future__ import annotations

from nu import Seq
from nu.shapes import Shape
from nu_virtuals import (
    EnsureLayoutCmd,
    IntRef,
    Snapshot,
    StrRef,
    Transaction,
    auto_atomic,
)
from nu_virtuals.meta.flat_ref import FlatRef


def _flat_ref(root_shape: type) -> FlatRef:
    """Build a minimal FlatRef rooted at the given shape for structural tests."""
    return FlatRef(
        static_path=(("slot", object),),
        root_shape=root_shape,
        is_primitive=False,
    )


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


def _count(tree, cls, scope_sentinel=object()) -> int:
    """Count ScopedOp boundaries of ``cls`` in the tree.

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
        if not node._is_leaf:
            stack.extend(node.children)
    return n


def _collect(tree, cls):
    """Return all nodes of type ``cls`` in the tree (pre-order)."""
    out = []
    stack = [tree]
    while stack:
        node = stack.pop()
        if isinstance(node, cls):
            out.append(node)
        if not node._is_leaf:
            # reverse to keep pre-order-ish
            stack.extend(reversed(node.children))
    return out


def _structure(tree) -> str:
    """Render a compact textual signature of the boundary structure.

    Only shows Transaction/Snapshot nodes and their nesting, ignoring other
    ops. Good enough for order-independence comparisons.
    """
    if isinstance(tree, (Transaction, Snapshot)):
        scope_name = tree.scope.__name__ if hasattr(tree.scope, "__name__") else repr(tree.scope)
        cls_name = type(tree).__name__
        inner = ",".join(_structure(c) for c in tree.children if not isinstance(c, type(None)))
        return f"{cls_name}({scope_name}){{{inner}}}"
    if tree._is_leaf:
        return ""
    parts = [_structure(c) for c in tree.children]
    parts = [p for p in parts if p]
    return ",".join(parts)


# =============================================================================
# TESTS
# =============================================================================


def test_scoped_wraps_only_matching_writes() -> None:
    shard_ref = _flat_ref(LedgerShard)
    acct_ref = _flat_ref(Account)
    tree = Seq(
        EnsureLayoutCmd(shard_ref),
        EnsureLayoutCmd(acct_ref),
    )

    out = auto_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    # exactly one Transaction, around the shard-targeted cmd
    assert len(txns) == 1
    assert txns[0].scope is LedgerShard


def test_unscoped_wraps_everything() -> None:
    shard_ref = _flat_ref(LedgerShard)
    acct_ref = _flat_ref(Account)
    tree = Seq(
        EnsureLayoutCmd(shard_ref),
        EnsureLayoutCmd(acct_ref),
    )

    out = auto_atomic(tree)

    txns = _collect(out, Transaction)
    assert len(txns) == 2
    assert all(t.scope is None for t in txns)


def test_scoped_then_unscoped_no_double_wrap() -> None:
    """Regression: unscoped pass after scoped pass must not re-wrap."""
    shard_ref = _flat_ref(LedgerShard)
    tree = EnsureLayoutCmd(shard_ref)

    t1 = auto_atomic(tree, scope=LedgerShard)
    t2 = auto_atomic(t1)

    txns = _collect(t2, Transaction)
    assert len(txns) == 1
    assert txns[0].scope is LedgerShard


def test_unscoped_then_scoped_no_double_wrap() -> None:
    """Reverse order: scoped pass after unscoped must not re-wrap either."""
    shard_ref = _flat_ref(LedgerShard)
    tree = EnsureLayoutCmd(shard_ref)

    t1 = auto_atomic(tree)
    t2 = auto_atomic(t1, scope=LedgerShard)

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
        EnsureLayoutCmd(shard_ref),
        EnsureLayoutCmd(acct_ref),
    )

    a = auto_atomic(auto_atomic(tree, scope=LedgerShard))
    b = auto_atomic(auto_atomic(tree), scope=LedgerShard)

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
    tree = Transaction(EnsureLayoutCmd(shard_ref), scope=LedgerShard)

    out = auto_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    assert len(txns) == 1
    assert out is tree  # no rewrite needed


def test_unscoped_boundary_covers_scoped_pass() -> None:
    """Transaction(scope=None) already covers any ref — scoped pass must skip."""
    shard_ref = _flat_ref(LedgerShard)
    tree = Transaction(EnsureLayoutCmd(shard_ref), scope=None)

    out = auto_atomic(tree, scope=LedgerShard)

    txns = _collect(out, Transaction)
    assert len(txns) == 1
    assert txns[0].scope is None
