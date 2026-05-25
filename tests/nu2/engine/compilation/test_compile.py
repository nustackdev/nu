"""Unit tests for ``nu2.engine.compilation.compile``.

The driver wires the three acts -- index, attribute sweeps, emit -- into
one call. These tests verify the cross-cutting invariants that hold after
a full compile, plus the failure shape on a non-finalized schema.
"""

from __future__ import annotations

import pytest
from _support.terms import Leaf, Node

from nu2.engine.compilation import compile
from nu2.engine.structure import NotFinalizedError, Schema, Synthesized


# --- consistency after a full compile -----------------------------------


def test_compile_fills_every_column_to_the_same_length(schema):
    schema.register(
        Synthesized(
            name="size",
            base=lambda program, path: 1,
            combine=lambda own, children: own + sum(children),
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf(), Node(Leaf())), schema)
    n = len(p.terms)
    assert len(p.children) == n
    assert len(p.parent_id) == n
    assert len(p.path_of) == n
    assert len(p.id_of) == n
    assert len(p.thunks) == n
    assert len(p.athunks) == n
    assert all(len(col) == n for col in p.attrs.values())


def test_id_of_round_trips_with_path_of(schema):
    schema.finalize()
    p = compile(Node(Leaf(), Node(Leaf())), schema)
    for nid, path in enumerate(p.path_of):
        assert p.id_of[path] == nid


def test_compile_runs_all_three_acts(schema):
    # One witness per act in a single program.
    schema.register(
        Synthesized(
            name="size",
            base=lambda program, path: 1,
            combine=lambda own, children: own + sum(children),
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    # Index act:
    assert p.path_of == [(), (0,), (1,)]
    # Attribute-sweep act:
    assert p.attrs["size"] == [3, 1, 1]
    # Emit act:
    assert all(t is not None for t in p.thunks)


# --- failure shape ------------------------------------------------------


def test_compile_against_a_non_finalized_schema_raises():
    schema = Schema()
    with pytest.raises(NotFinalizedError):
        compile(Leaf(), schema)
