"""Unit tests for ``nu.engine.compilation.emit``.

Covers ``emit_thunks`` -- the reverse-preorder pass that builds the sync
and async per-node thunks. Each thunk receives its children's precompiled
thunks; the default ``Term.compile`` produces a thunk that defers to
``Term.eval``.
"""

from __future__ import annotations

import pytest
from _support.terms import Leaf, Node

from nu.engine.compilation import compile
from nu.engine.structure import Schema, Term


# --- thunk columns are dense ---------------------------------------------


def test_thunks_and_athunks_are_one_per_nid(schema):
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    assert len(p.thunks) == 3
    assert len(p.athunks) == 3
    assert all(t is not None for t in p.thunks)
    assert all(t is not None for t in p.athunks)


# --- the default Term contract surfaces at thunk-call time ---------------


def test_default_compile_thunk_defers_to_eval_at_call_time(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    with pytest.raises(NotImplementedError, match=r"Leaf\.eval"):
        p.thunks[0](None)


# --- reverse-preorder guarantee: children built before parents -----------


def test_an_overridden_compile_captures_children_already_built():
    captured: dict[int, tuple] = {}

    class Recorder(Term):
        def compile(self, nid, children):
            captured[nid] = children

            def thunk(rt):
                return nid

            return thunk

        def acompile(self, nid, children):
            async def athunk(rt):
                return nid

            return athunk

    schema = Schema().finalize()
    p = compile(Recorder(Recorder(), Recorder()), schema)
    # Root nid 0 captures its two children's thunks; those are the same
    # closures the emit pass stored at thunks[1] and thunks[2].
    assert len(captured[0]) == 2
    assert captured[0][0] is p.thunks[1]
    assert captured[0][1] is p.thunks[2]
    # Leaves get empty child tuples.
    assert captured[1] == ()
    assert captured[2] == ()


# --- async path ----------------------------------------------------------


async def test_an_overridden_acompile_yields_an_awaitable_thunk():
    class AsyncLeaf(Term):
        def acompile(self, nid, children):
            async def athunk(rt):
                return 42

            return athunk

    schema = Schema().finalize()
    p = compile(AsyncLeaf(), schema)
    assert await p.athunks[0](None) == 42
