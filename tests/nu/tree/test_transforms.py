"""Tests for nu.tree.rewrite: generic structural Nu -> Nu transforms.

compose, apply, map_children, map_nodes, replace, wrap, unwrap, graft,
prune, conditional_wrap. Pure structural -- built on Sequential branches +
Literal leaves, never compiled.
"""

from __future__ import annotations

from nu.core import Literal
from nu.flows import Sequential
from nu.tree import (
    apply,
    compose,
    conditional_wrap,
    find,
    graft,
    map_children,
    map_nodes,
    prune,
    replace,
    unwrap,
    wrap,
)


def _vals(nodes):
    return [n._payload["value"] for n in nodes if isinstance(n, Literal)]


def _is_seq(n):
    return isinstance(n, Sequential)


def _leaf_is(v):
    return lambda n: isinstance(n, Literal) and n._payload["value"] == v


def _tree():
    """root[ 1, mid[ 2, 3 ], 4 ]."""
    return Sequential(
        Literal(1),
        Sequential(Literal(2), Literal(3)),
        Literal(4),
    )


# --- map ordering ---------------------------------------------------------


def test_map_nodes_bottom_up_visits_children_first():
    root = _tree()
    log: list = []

    def visit(n):
        log.append(n._payload["value"] if isinstance(n, Literal) else "S")
        return n

    map_nodes(root, visit, order="bottom_up")
    assert log == [1, 2, 3, "S", 4, "S"]  # postorder


def test_map_nodes_top_down_visits_parent_first():
    root = _tree()
    log: list = []

    def visit(n):
        log.append(n._payload["value"] if isinstance(n, Literal) else "S")
        return n

    map_nodes(root, visit, order="top_down")
    assert log == ["S", 1, "S", 2, 3, 4]  # preorder


def test_map_children_is_shallow():
    root = _tree()
    seen: list = []

    def visit(n):
        seen.append(n)
        return n

    map_children(root, visit)
    assert len(seen) == 3  # only direct children


# --- replace / wrap -------------------------------------------------------


def test_replace_swaps_matching_leaves():
    root = _tree()
    out = replace(root, _leaf_is(2), lambda _: Literal(20))
    assert sorted(_vals(find(out, lambda n: isinstance(n, Literal)))) == [1, 3, 4, 20]


def test_wrap_wraps_matching_node():
    root = _tree()
    out = wrap(root, _leaf_is(2), lambda n: Sequential(n))
    # the matched leaf now sits under an extra Sequential wrapper
    wrapped = find(out, lambda n: isinstance(n, Sequential) and len(n._children) == 1)
    assert len(wrapped) == 1
    assert wrapped[0]._children[0]._payload["value"] == 2


def test_unwrap_splices_single_child_wrappers():
    root = Sequential(Sequential(Literal(5)), Literal(6))
    out = unwrap(root, _is_seq)
    # the inner single-child Sequential is gone; its child is spliced up
    assert _vals(out._children) == [5, 6]


# --- graft / prune --------------------------------------------------------


def test_graft_replaces_target_by_identity():
    a = Literal(1)
    root = Sequential(a, Literal(2))
    out = graft(root, a, Literal(100))
    assert _vals(out._children) == [100, 2]


def test_prune_removes_matching_subtrees():
    root = _tree()
    out = prune(root, _leaf_is(2))
    assert sorted(_vals(find(out, lambda n: isinstance(n, Literal)))) == [1, 3, 4]


def test_prune_returns_none_when_root_matches():
    assert prune(Literal(1), _leaf_is(1)) is None


def test_prune_preserves_identity_when_nothing_matches():
    root = _tree()
    assert prune(root, _leaf_is(99)) is root


# --- conditional_wrap -----------------------------------------------------


def test_conditional_wrap_claims_matching_child_whole():
    root = _tree()  # root has 3 children; mid has 2

    def is_pair(n):
        return isinstance(n, Sequential) and len(n._children) == 2

    out = conditional_wrap(root, is_pair, lambda n: Sequential(n))
    # root does not match (3 children) so we recurse; mid matches -> wrapped whole
    mid_wrapper = out._children[1]
    assert isinstance(mid_wrapper, Sequential)
    assert len(mid_wrapper._children) == 1
    assert _vals(mid_wrapper._children[0]._children) == [2, 3]


# --- compose / apply ------------------------------------------------------


def test_compose_runs_left_to_right():
    root = _tree()

    def f(r):
        return replace(r, _leaf_is(1), lambda _: Literal(10))

    def g(r):
        return replace(r, _leaf_is(4), lambda _: Literal(40))

    out = compose(f, g)(root)
    assert sorted(_vals(find(out, lambda n: isinstance(n, Literal)))) == [2, 3, 10, 40]


def test_apply_threads_transforms_in_order():
    root = _tree()
    out = apply(
        root,
        lambda r: replace(r, _leaf_is(1), lambda _: Literal(10)),
        lambda r: replace(r, _leaf_is(10), lambda _: Literal(11)),
    )
    assert sorted(_vals(find(out, lambda n: isinstance(n, Literal)))) == [2, 3, 4, 11]
