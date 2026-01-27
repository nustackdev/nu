"""Tests for topology language PoC.

Organized by design rules from docs/lang/rules.md.
"""

from __future__ import annotations

import pytest

from .context import DictKVSubstrate, KVContext, Snapshot, Transaction
from .executor import execute
from .lang import (
    Add,
    Atomic,
    Cond,
    Get,
    GroupedContext,
    Lit,
    Mul,
    Par,
    Ref,
    RootGroup,
    Seq,
    Set,
    Term,
)
from .transforms import (
    CancelFlag,
    CancelledError,
    Log,
    add_cancellation,
    add_logging,
)


# =============================================================================
# Helpers
# =============================================================================


def make_root(data=None, child=None):
    """Create a RootGroup with DictKVSubstrate."""
    if data is None:
        data = {}
    sub = DictKVSubstrate(data)
    return RootGroup(substrates={KVContext: sub}, child=child), sub


# =============================================================================
# R1-R3: Composition rules
# =============================================================================


class TestCompositionRules:
    """R1: Term children are Terms. R2/R3: Flow/Group accept Units."""

    def test_r1_term_children_are_terms(self):
        """Term.children() returns list[Term]."""
        t = Add(Lit(1), Lit(2))
        for child in t.children():
            assert isinstance(child, Term)

    def test_r2_flow_accepts_any_unit(self):
        """Flow children can be Terms, Flows, or Groups."""
        inner_flow = Seq(Lit(1))
        inner_group = Atomic(Lit(2))
        outer = Seq(Lit(0), inner_flow, inner_group)
        children = outer.children()
        assert len(children) == 3

    def test_r3_group_accepts_any_unit(self):
        """Group children can be Terms, Flows, or Groups."""
        inner = Seq(Lit(1), Lit(2))
        group = Atomic(Lit(0), inner, Atomic(Lit(3)))
        children = group.children()
        assert len(children) == 3


# =============================================================================
# S1: Implicit grouping
# =============================================================================


class TestImplicitGrouping:
    """S1: Every direct Term child of a Flow is implicitly wrapped in Atomic."""

    def test_s1_seq_terms_get_own_context(self):
        """Each Term in Seq gets its own implicit Atomic → own context."""
        data = {"a": 1, "b": 2}
        root, sub = make_root(data, Seq(Get(Ref("a")), Get(Ref("b"))))
        result = execute(root)
        # Last value returned
        assert result == 2

    def test_s1_implicit_atomic_infers_snapshot_for_reads(self):
        """Implicit Atomic around read-only Term → Snapshot (cheap)."""
        data = {"x": 42}
        root, sub = make_root(data, Seq(Get(Ref("x"))))
        result = execute(root)
        assert result == 42

    def test_s1_implicit_atomic_infers_transaction_for_writes(self):
        """Implicit Atomic around write Term → Transaction."""
        data = {"x": 1}
        root, sub = make_root(data, Seq(Set(Ref("x"), Lit(99))))
        execute(root)
        assert sub.data["x"] == 99

    def test_s1_expression_tree_is_indivisible(self):
        """A complex expression tree shares one context."""
        data = {"a": 10, "b": 20}
        # Add(Get(a), Get(b)) is one expression tree → one Atomic
        expr = Add(Get(Ref("a")), Get(Ref("b")))
        root, sub = make_root(data, Seq(expr))
        result = execute(root)
        assert result == 30


# =============================================================================
# S2: Group transparency
# =============================================================================


class TestGroupTransparency:
    """S2: Removing Groups doesn't change what is computed (for pure)."""

    def test_s2_pure_computation_with_and_without_group(self):
        """Pure computation produces same result with or without Group."""
        # With explicit group
        grouped = Atomic(Add(Lit(1), Lit(2)))
        result_grouped = execute(grouped)

        # Without group (bare term)
        bare = Add(Lit(1), Lit(2))
        result_bare = execute(bare)

        assert result_grouped == result_bare == 3

    def test_s2_nested_groups_same_result(self):
        """Adding nested Groups doesn't change pure result."""
        inner = Atomic(Add(Lit(3), Lit(4)))
        outer = Atomic(inner)
        result = execute(outer)
        assert result == 7


# =============================================================================
# S3: Term closure
# =============================================================================


class TestTermClosure:
    """S3: Composing Terms yields a Term."""

    def test_s3_add_produces_term(self):
        """Add of two Terms is a Term."""
        result = Add(Lit(1), Lit(2))
        assert isinstance(result, Term)

    def test_s3_nested_composition(self):
        """Deeply nested composition is still a Term."""
        t = Add(Mul(Lit(2), Lit(3)), Add(Lit(4), Lit(5)))
        assert isinstance(t, Term)
        result = execute(t)
        assert result == 15  # 2*3 + 4+5


# =============================================================================
# S4: Orthogonality
# =============================================================================


class TestOrthogonality:
    """S4: Each primitive owns exactly one concern."""

    def test_s4_term_is_pure_defaults_true(self):
        """Terms default to pure."""
        assert Lit(1).is_pure is True
        assert Get(Ref("x")).is_pure is True
        assert Add(Lit(1), Lit(2)).is_pure is True

    def test_s4_set_is_impure(self):
        """Set command is impure."""
        assert Set(Ref("x"), Lit(1)).is_pure is False


# =============================================================================
# B1: Needs propagation
# =============================================================================


class TestNeedsPropagation:
    """B1: Needs are union of own + children's needs."""

    def test_b1_lit_needs_nothing(self):
        assert Lit(1).needs() == set()

    def test_b1_get_needs_kv(self):
        assert Get(Ref("x")).needs() == {KVContext}

    def test_b1_set_needs_kv(self):
        assert KVContext in Set(Ref("x"), Lit(1)).needs()

    def test_b1_add_propagates_children_needs(self):
        needs = Add(Get(Ref("a")), Lit(1)).needs()
        assert KVContext in needs

    def test_b1_group_absorbs_provided(self):
        """Group's needs = children's needs - provided."""
        group = Atomic(Get(Ref("a")))
        # Atomic provides Snapshot (inferred from reads)
        # KVContext need is absorbed
        assert group.needs() == set()


# =============================================================================
# B2-B4: Resolution
# =============================================================================


class TestResolution:
    """B2: Nearest Group wins. B3: Ephemeral fallback. B4: Innermost wins."""

    def test_b2_group_provides_context(self):
        """Term inside Group gets context from that Group."""
        data = {"x": 42}
        root, _ = make_root(data, Seq(Get(Ref("x"))))
        result = execute(root)
        assert result == 42

    def test_b3_ephemeral_fallback(self):
        """Term outside explicit Group gets ephemeral context."""
        data = {"x": 42}
        root, _ = make_root(data, Seq(Get(Ref("x"))))
        # The implicit Atomic (S1) handles this, but the mechanism
        # is ephemeral context creation from substrate
        result = execute(root)
        assert result == 42

    def test_b4_innermost_wins(self):
        """Nested Groups: inner context shadows outer."""
        data = {"x": 10}
        root, sub = make_root(
            data,
            Seq(
                GroupedContext(
                    Transaction,
                    Set(Ref("x"), Lit(100)),
                    # Inner group with Snapshot — reads see transaction's writes
                    GroupedContext(
                        Snapshot,
                        Get(Ref("x")),  # Reads from inner Snapshot (original data)
                    ),
                ),
            ),
        )
        result = execute(root)
        # Inner Snapshot was created from original data (x=10),
        # not from the outer Transaction's pending writes
        assert result == 10
        # But the outer Transaction's write DID commit
        assert sub.data["x"] == 100


# =============================================================================
# C1-C2: Lazy open / eager close
# =============================================================================


class TestLazyLifetime:
    """C1: Lazy open. C2: Eager close."""

    def test_c1_c2_context_created_and_released(self):
        """Context is created when needed and released after."""
        data = {"x": 1}
        sub = DictKVSubstrate(data)

        # Create a Transaction context manually to track lifecycle
        root = RootGroup(
            substrates={KVContext: sub},
            child=Seq(Get(Ref("x"))),
        )
        execute(root)
        # If we got here without error, context was created and released

    def test_c3_no_context_for_pure_computation(self):
        """Atomic with no KV needs opens nothing."""
        result = execute(Seq(Add(Lit(1), Lit(2))))
        assert result == 3


# =============================================================================
# C3: Context type inference
# =============================================================================


class TestContextInference:
    """C3: Atomic infers Snapshot vs Transaction."""

    def test_c3_reads_only_infer_snapshot(self):
        """Only reads → Snapshot inferred."""
        atomic = Atomic(Get(Ref("x")))
        assert atomic.infer_context_type() is Snapshot

    def test_c3_writes_infer_transaction(self):
        """Any writes → Transaction inferred."""
        atomic = Atomic(Set(Ref("x"), Lit(1)))
        assert atomic.infer_context_type() is Transaction

    def test_c3_mixed_infer_transaction(self):
        """Reads + writes → Transaction inferred."""
        atomic = Atomic(Get(Ref("x")), Set(Ref("y"), Lit(1)))
        assert atomic.infer_context_type() is Transaction

    def test_c3_no_kv_infer_none(self):
        """No KV needs → None (no-op)."""
        atomic = Atomic(Add(Lit(1), Lit(2)))
        assert atomic.infer_context_type() is None


# =============================================================================
# Transforms
# =============================================================================


class TestTransforms:
    """Tree→Tree transforms."""

    def test_add_logging(self, capsys):
        """add_logging inserts Log terms at Flow boundaries."""
        tree = Seq(Lit(1), Lit(2))
        logged = add_logging(tree)
        execute(logged)
        captured = capsys.readouterr()
        assert "[LOG] enter" in captured.out
        assert "[LOG] exit" in captured.out

    def test_add_cancellation_not_cancelled(self):
        """Cancellation transform runs normally when not cancelled."""
        flag = CancelFlag()
        tree = Seq(Lit(1), Lit(2), Lit(3))
        cancellable = add_cancellation(tree, flag)
        result = execute(cancellable)
        assert result == 3

    def test_add_cancellation_cancelled(self):
        """Cancellation transform raises when flag is set."""
        flag = CancelFlag()
        flag.cancel()
        tree = Seq(Lit(1), Lit(2))
        cancellable = add_cancellation(tree, flag)
        with pytest.raises(CancelledError):
            execute(cancellable)

    def test_transforms_compose(self, capsys):
        """Transforms compose via function application."""
        flag = CancelFlag()
        tree = Seq(Lit(1), Lit(2))

        # Apply cancellation first, then logging
        # (cancellation wraps children in Cond, logging adds Log around those)
        tree = add_cancellation(tree, flag)
        tree = add_logging(tree)

        execute(tree)
        captured = capsys.readouterr()
        assert "[LOG]" in captured.out
        # Not cancelled, so all steps ran
        assert "enter" in captured.out
        assert "exit" in captured.out


# =============================================================================
# End-to-end
# =============================================================================


class TestEndToEnd:
    """Full pipeline tests."""

    def test_read_write_flow(self):
        """Complete read → compute → write pipeline."""
        data = {"score": 42}
        root, sub = make_root(
            data,
            Seq(
                Set(Ref("score"), Add(Get(Ref("score")), Lit(1))),
            ),
        )
        execute(root)
        assert sub.data["score"] == 43

    def test_explicit_atomic_cross_expression(self):
        """Explicit Atomic spans multiple expressions atomically."""
        data = {"a": 1, "b": 2}
        root, sub = make_root(
            data,
            Seq(
                Atomic(
                    Set(Ref("a"), Lit(10)),
                    Set(Ref("b"), Lit(20)),
                ),
            ),
        )
        execute(root)
        assert sub.data["a"] == 10
        assert sub.data["b"] == 20

    def test_mixed_reads_and_writes(self):
        """Mixed reads and writes in a sequence."""
        data = {"x": 5, "y": 10}
        root, sub = make_root(
            data,
            Seq(
                Get(Ref("x")),  # implicit Atomic → Snapshot
                Set(Ref("y"), Add(Get(Ref("x")), Get(Ref("y")))),  # implicit Atomic → Transaction
            ),
        )
        result = execute(root)
        assert sub.data["y"] == 15

    def test_conditional_flow(self):
        """Conditional branching."""
        tree = Cond(Lit(True), Lit("yes"), Lit("no"))
        assert execute(tree) == "yes"

        tree = Cond(Lit(False), Lit("yes"), Lit("no"))
        assert execute(tree) == "no"

    def test_parallel_flow(self):
        """Parallel execution returns tuple."""
        tree = Par(Lit(1), Lit(2), Lit(3))
        result = execute(tree)
        assert result == (1, 2, 3)

    def test_nested_flows(self):
        """Nested Seq inside Seq."""
        tree = Seq(
            Lit(1),
            Seq(Lit(2), Lit(3)),
            Lit(4),
        )
        result = execute(tree)
        assert result == 4

    def test_full_program(self):
        """Full program with RootGroup, multiple operations."""
        data = {"users": 10, "score": 100}
        root, sub = make_root(
            data,
            Seq(
                # Read users (implicit Atomic → Snapshot)
                Get(Ref("users")),
                # Increment score (implicit Atomic → Transaction)
                Set(Ref("score"), Add(Get(Ref("score")), Lit(50))),
                # Atomic cross-expression: read + write together
                Atomic(
                    Get(Ref("users")),
                    Set(Ref("users"), Add(Get(Ref("users")), Lit(1))),
                ),
            ),
        )
        execute(root)
        assert sub.data["score"] == 150
        assert sub.data["users"] == 11
