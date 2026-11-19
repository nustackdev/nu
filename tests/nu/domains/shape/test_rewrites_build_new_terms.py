"""Every ref rewrite builds new terms: the term it started from is left as it was.

``reroot``, ``with_parent``, ``ItemRef.to`` and the kv ``.lazy`` / ``.eager``
facets each hand back a variant. The source chain is snapshotted node by node
(type, fields, children identity) before the rewrite and compared after.
"""

from __future__ import annotations

import nu
from nu.domains.shape import Shape, reroot, with_parent
from nustd.kv import OrderedDictRef


class Counter(Shape):
    value = nu.IntRef.slot()


class Cells(Shape):
    pass


class State(Shape):
    cells = nu.DictRef.slot(Cells)
    anything = nu.DictRef.slot(object)


class Plane(Shape):
    cells = OrderedDictRef.slot(bool)


def snapshot(node) -> list[tuple]:
    """Each node under ``node``: its identity, type, fields and children ids."""
    out = []
    stack = [node]
    while stack:
        cur = stack.pop()
        kids = nu.tree.children(cur)
        out.append((id(cur), type(cur), nu.tree.fields(cur), tuple(map(id, kids))))
        stack.extend(kids)
    return out


def test_reroot_leaves_the_source_as_it_was():
    source = Counter.value
    before = snapshot(source)
    out = reroot(source, State.cells["c1"])
    assert out is not source
    assert snapshot(source) == before


def test_with_parent_leaves_the_source_as_it_was():
    source = Counter.value
    before = snapshot(source)
    placed = source.with_parent(State.cells["c1"])
    assert placed._placed
    assert not source._placed
    assert snapshot(source) == before


def test_with_parent_leaves_the_parent_as_it_was():
    parent = State.cells["c1"]
    before = snapshot(parent)
    with_parent(Counter.value, parent)
    assert snapshot(parent) == before


def test_to_leaves_the_source_as_it_was():
    placed = with_parent(Counter.value, State.cells["c1"])
    before = snapshot(placed)
    as_str = placed.to(nu.StrRef)
    assert as_str is not placed
    assert snapshot(placed) == before


def test_facets_leave_the_source_as_it_was():
    source = Plane.cells
    before = snapshot(source)
    eager = source.eager
    lazy = eager.lazy
    assert eager is not source
    assert lazy is not eager
    assert snapshot(source) == before
