"""Tests for auto_distribute deformation."""

from __future__ import annotations

from nu import Add, All, Any, Parallel, Print, Race, Seq
from nu.terms import Literal
from nu.tree import preorder
from nu_distributed import Teleport, auto_distribute
from nu_distributed.meta.auto_distribute import round_robin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _teleport_children(node):
    """Return list of (child, worker_tag) for Teleport children."""
    result = []
    for child in node.children:
        if isinstance(child, Teleport):
            result.append((child.children[0], child._worker_tag))
    return result


def _count_teleports(tree):
    """Count Teleport nodes in tree."""
    return sum(1 for node in preorder(tree) if isinstance(node, Teleport))


# ---------------------------------------------------------------------------
# Basic wrapping
# ---------------------------------------------------------------------------


class TestParallel:
    def test_parallel_children_wrapped(self):
        tree = Parallel(Print("a"), Print("b"), Print("c"))
        result = auto_distribute(tree)

        assert isinstance(result, Parallel)
        assert all(isinstance(c, Teleport) for c in result.children)
        assert len(result.children) == 3

    def test_worker_tags_round_robin(self):
        tree = Parallel(Print("a"), Print("b"), Print("c"))
        result = auto_distribute(tree)

        tags = [c._worker_tag for c in result.children]
        assert tags == [0, 1, 2]


class TestAll:
    def test_all_children_wrapped(self):
        tree = All(Print("a"), Print("b"))
        result = auto_distribute(tree)

        assert isinstance(result, All)
        assert all(isinstance(c, Teleport) for c in result.children)

    def test_preserves_all_semantics(self):
        """All node itself stays All - only children change."""
        tree = All(Print("a"), Print("b"))
        result = auto_distribute(tree)
        assert type(result) is All


class TestRace:
    def test_race_children_wrapped(self):
        tree = Race(Print("a"), Print("b"))
        result = auto_distribute(tree)

        assert isinstance(result, Race)
        assert all(isinstance(c, Teleport) for c in result.children)


class TestAny:
    def test_any_children_wrapped(self):
        tree = Any(Print("a"), Print("b"))
        result = auto_distribute(tree)

        assert isinstance(result, Any)
        assert all(isinstance(c, Teleport) for c in result.children)


# ---------------------------------------------------------------------------
# Skip existing Teleport
# ---------------------------------------------------------------------------


class TestSkipExisting:
    def test_already_teleported_skipped(self):
        tree = Parallel(
            Teleport(Print("a"), worker="gpu"),
            Print("b"),
        )
        result = auto_distribute(tree)

        # First child kept as-is (worker="gpu"), second wrapped
        assert isinstance(result.children[0], Teleport)
        assert result.children[0]._worker_tag == "gpu"
        assert isinstance(result.children[1], Teleport)
        assert result.children[1]._worker_tag == 1

    def test_all_already_teleported_unchanged(self):
        tree = Parallel(
            Teleport(Print("a"), worker=0),
            Teleport(Print("b"), worker=1),
        )
        result = auto_distribute(tree)

        # Nothing changed - same tree
        assert result is tree


# ---------------------------------------------------------------------------
# Non-concurrent ops untouched
# ---------------------------------------------------------------------------


class TestNonConcurrent:
    def test_seq_not_touched(self):
        tree = Seq(Print("a"), Print("b"))
        result = auto_distribute(tree)
        assert result is tree

    def test_pure_op_not_touched(self):
        tree = Add(Literal(1), Literal(2))
        result = auto_distribute(tree)
        assert result is tree


# ---------------------------------------------------------------------------
# Nested
# ---------------------------------------------------------------------------


class TestNested:
    def test_nested_parallel_in_seq(self):
        tree = Seq(
            Print("before"),
            Parallel(Print("a"), Print("b")),
            Print("after"),
        )
        result = auto_distribute(tree)

        assert isinstance(result, Seq)
        # Seq itself unchanged, but inner Parallel has Teleports
        par = result.children[1]
        assert isinstance(par, Parallel)
        assert all(isinstance(c, Teleport) for c in par.children)
        # Seq's direct children Print("before") and Print("after") not wrapped
        assert not isinstance(result.children[0], Teleport)
        assert not isinstance(result.children[2], Teleport)

    def test_nested_concurrent_ops(self):
        """Parallel inside All - both get distributed."""
        tree = All(
            Parallel(Print("a"), Print("b")),
            Print("c"),
        )
        result = auto_distribute(tree)

        # All's children are wrapped
        assert isinstance(result, All)
        assert all(isinstance(c, Teleport) for c in result.children)
        # Inner Parallel's children are also wrapped (bottom-up)
        inner_par = result.children[0].children[0]
        assert isinstance(inner_par, Parallel)
        assert all(isinstance(c, Teleport) for c in inner_par.children)

    def test_deep_nesting(self):
        tree = Seq(
            Parallel(
                All(Print("a"), Print("b")),
                Race(Print("c"), Print("d")),
            ),
        )
        result = auto_distribute(tree)
        # 4 inner + 2 outer = 6 teleports
        assert _count_teleports(result) == 6


# ---------------------------------------------------------------------------
# Custom strategy
# ---------------------------------------------------------------------------


class TestStrategy:
    def test_custom_strategy(self):
        def by_machine(index: int, count: int) -> tuple[str, int]:
            machines = ["red", "blue"]
            return (machines[index % len(machines)], index)

        tree = Parallel(Print("a"), Print("b"), Print("c"))
        result = auto_distribute(tree, strategy=by_machine)

        tags = [c._worker_tag for c in result.children]
        assert tags == [("red", 0), ("blue", 1), ("red", 2)]

    def test_single_worker_strategy(self):
        tree = Parallel(Print("a"), Print("b"))
        result = auto_distribute(tree, strategy=lambda i, c: 0)

        tags = [c._worker_tag for c in result.children]
        assert tags == [0, 0]


# ---------------------------------------------------------------------------
# Empty
# ---------------------------------------------------------------------------


class TestEmpty:
    def test_empty_parallel(self):
        tree = Parallel()
        result = auto_distribute(tree)
        assert result is tree

    def test_single_child(self):
        tree = Parallel(Print("alone"))
        result = auto_distribute(tree)
        assert isinstance(result.children[0], Teleport)


# ---------------------------------------------------------------------------
# round_robin
# ---------------------------------------------------------------------------


class TestRoundRobin:
    def test_round_robin(self):
        assert round_robin(0, 3) == 0
        assert round_robin(1, 3) == 1
        assert round_robin(2, 3) == 2
