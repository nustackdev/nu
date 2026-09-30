"""The law gate over ``nustd.mp_pool`` trees. No processes: this is compile-time only."""

from __future__ import annotations

import pytest

import nu
import nustd
from nu.lang.attributes import Cardinality, Sort
from nustd.mp_pool import (
    Alive,
    Dispatch,
    Kill,
    Launch,
    PoolRef,
    Running,
    Teleport,
    Wait,
    WorkerPool,
    Workers,
)


class Scratch(nu.Shape):
    """Where these trees put what they read, and the worker they address."""

    n = nustd.mem.ObjectRef.slot()
    m = nustd.mem.ObjectRef.slot()
    w = nustd.mem.ObjectRef.slot()
    a = nustd.mem.ObjectRef.slot()
    r = nustd.mem.ObjectRef.slot()
    c = nustd.mem.ObjectRef.slot()
    ws = nustd.mem.ObjectRef.slot()


RESIDENT = nu.ForeverDo(nu.DelayedDo(0.01, Scratch.n.set(1)))


def _provided(body: nu.Nu) -> nu.Nu:
    return nu.Provide(WorkerPool, {"name": "laws"}, body)


TREES = {
    "launch": _provided(Scratch.w.set(Launch())),
    "launch_with_init": _provided(
        Scratch.w.set(Launch(init=nu.Provide(dict, {}))),
    ),
    "dispatch": _provided(Dispatch(body=RESIDENT, worker=Scratch.w)),
    "dispatch_command_body": _provided(
        Dispatch(body=Scratch.n.set(1), worker=Scratch.w),
    ),
    "teleport_scalar": _provided(Teleport(body=nu.Add(1, 2), worker=Scratch.w)),
    "teleport_command": _provided(
        Teleport(body=Scratch.n.set(1), worker=Scratch.w),
    ),
    "kill": _provided(Kill(worker=Scratch.w)),
    "alive": _provided(Scratch.a.set(Alive(worker=Scratch.w))),
    "running": _provided(Scratch.r.set(Running(worker=Scratch.w))),
    "wait": _provided(Scratch.c.set(Wait(worker=Scratch.w))),
    "workers": _provided(Scratch.ws.set(nu.Collect(Workers()))),
    "explicit_pool_ref": _provided(
        nustd.mem.Frame(
            Scratch,
            Teleport(PoolRef(), body=nu.Add(1, 1), worker=Scratch.w),
            w=Launch(PoolRef()),
        ),
    ),
    "fluent": _provided(
        nustd.mem.Frame(
            Scratch,
            nu.Sequential(
                PoolRef().dispatch(RESIDENT, Scratch.w),
                PoolRef().teleport(Scratch.n.set(1), Scratch.w),
                PoolRef().kill(Scratch.w),
            ),
            w=PoolRef().launch(),
        ),
    ),
    "fluent_reads": _provided(
        nu.Sequential(
            Scratch.a.set(PoolRef().alive(Scratch.w)),
            Scratch.r.set(PoolRef().running(Scratch.w)),
            Scratch.c.set(PoolRef().wait(Scratch.w)),
            Scratch.ws.set(nu.Collect(PoolRef().workers())),
        ),
    ),
    "dispatch_forever_body": _provided(
        Dispatch(body=nu.ForeverDo(Scratch.n.set(1)), worker=Scratch.w),
    ),
    "whole_lifecycle": _provided(
        nustd.mem.Frame(
            Scratch,
            nu.Sequential(
                Teleport(body=Scratch.n.set(0), worker=Scratch.w),
                Dispatch(body=RESIDENT, worker=Scratch.w),
                Kill(worker=Scratch.w),
            ),
            w=Launch(),
        ),
    ),
}


@pytest.mark.parametrize("name", sorted(TREES))
def test_validate_passes(name):
    nu.validate(nu.compile(TREES[name]))


def test_dispatching_a_query_is_allowed():
    """A dispatched body's value is dropped by design, whatever it yields."""
    assert nu.tree.payload(Dispatch(body=nu.Add(1, 2), worker=Scratch.w))["body"] is not None


def test_dispatching_a_non_nu_body_is_refused():
    with pytest.raises(TypeError, match="needs a Nu body"):
        Dispatch(body=42, worker=Scratch.w)


def test_kill_without_a_ref_in_its_mutation_slot_is_refused():
    """``ref_slots``: a VOID mutator has to land its write through a Ref."""
    tree = Kill(nu.Literal(object()), 0)
    with pytest.raises(Exception, match="slot 0 must hold a Ref"):
        nu.validate(nu.compile(tree))


def test_dispatch_without_a_ref_in_its_mutation_slot_is_refused():
    """Same law, and the reason the pool ref has to stay slot 0 of a Command."""
    tree = Dispatch(nu.Literal(object()), RESIDENT, 0)
    with pytest.raises(Exception, match="slot 0 must hold a Ref"):
        nu.validate(nu.compile(tree))


# --- the sorts --------------------------------------------------------------


def test_dispatch_is_a_void_command():
    """A Command, not a Control: a mutating Control was the shape that was rejected."""
    node = Dispatch(body=RESIDENT, worker=7)
    assert isinstance(node, nu.Command)
    assert not isinstance(node, nu.Flow)
    assert type(node)._attributes["sort"].value is Sort.SCALAR_COMMAND
    assert type(node)._attributes["cardinality"].value is Cardinality.VOID
    assert type(node)._attributes["mutates"].value == frozenset({0})
    assert "param_slots" not in type(node).__dict__


@pytest.mark.parametrize(
    "body",
    [
        nu.ForeverDo(Scratch.n.set(1)),
        nu.ReactForever(Scratch.n, Scratch.m.set(1)),
        nu.Sequential(Scratch.n.set(1)),
        Scratch.n.set(1),
    ],
)
def test_a_flow_body_is_accepted_and_the_tree_still_validates(body):
    """The whole point of the payload: a Flow body a Command could not hold."""
    node = Dispatch(body=body, worker=Scratch.w)
    assert nu.tree.payload(node)["body"] is body
    nu.validate(nu.compile(_provided(node)))


# --- the fluent interface ---------------------------------------------------


def _same_shape(a: nu.Nu, b: nu.Nu) -> bool:
    """Structural equality by class, payload and child shape, recursively."""
    return (
        type(a) is type(b)
        and nu.tree.payload(a) == nu.tree.payload(b)
        and len(nu.tree.children(a)) == len(nu.tree.children(b))
        and all(
            _same_shape(x, y) for x, y in zip(nu.tree.children(a), nu.tree.children(b), strict=True)
        )
    )


FLUENT = [
    (lambda p: p.launch(), lambda p: Launch(p)),
    (lambda p: p.dispatch(RESIDENT, 7), lambda p: Dispatch(p, RESIDENT, 7)),
    (lambda p: p.dispatch(RESIDENT, 7, carry=True), lambda p: Dispatch(p, RESIDENT, 7, carry=True)),
    (lambda p: p.teleport(RESIDENT, 7), lambda p: Teleport(p, RESIDENT, 7)),
    (lambda p: p.teleport(RESIDENT, 7, carry=True), lambda p: Teleport(p, RESIDENT, 7, carry=True)),
    (lambda p: p.kill(7), lambda p: Kill(p, 7)),
    (lambda p: p.alive(7), lambda p: Alive(p, 7)),
    (lambda p: p.running(7), lambda p: Running(p, 7)),
    (lambda p: p.wait(7), lambda p: Wait(p, 7)),
    (lambda p: p.workers(), lambda p: Workers(p)),
]


@pytest.mark.parametrize(("fluent", "direct"), FLUENT)
def test_the_fluent_form_builds_the_same_term(fluent, direct):
    assert _same_shape(fluent(PoolRef()), direct(PoolRef()))


def test_the_fluent_form_puts_the_receiver_in_the_pool_slot():
    ref = PoolRef()
    assert nu.tree.children(ref.kill(7))[0] is ref
    assert nu.tree.children(ref.launch())[0] is ref
    assert nu.tree.children(ref.workers())[0] is ref
    # Teleport's pool slot is children[1]; the body is children[0] by Span rule.
    assert nu.tree.children(ref.teleport(RESIDENT, 7))[1] is ref


def test_the_fluent_dispatch_still_keeps_its_body_in_payload():
    assert nu.tree.payload(PoolRef().dispatch(RESIDENT, 7))["body"] is RESIDENT


# --- children vs payload ----------------------------------------------------


def test_the_atoms_carry_no_caller_value_in_payload():
    """The design constraint: ids and targets are children, the body excepted."""
    atoms = [
        Launch(init=nu.Provide(dict, {})),
        Dispatch(body=RESIDENT, worker=7),
        Teleport(body=nu.Add(1, 2), worker=7),
        Kill(worker=7),
        Alive(worker=7),
        Running(worker=7),
        Wait(worker=7),
        Workers(),
    ]
    for atom in atoms:
        # A body is a term, and `==` on a term builds a comparison: skip them.
        assert 7 not in [v for v in nu.tree.payload(atom).values() if not isinstance(v, nu.Nu)]
        assert set(nu.tree.payload(atom)) <= {"carry", "body"}
    # And the pool ref itself, unlike the tag nustd.mp's MpWorkerRef used to hold.
    assert nu.tree.payload(PoolRef()) == {}
    assert len(nu.tree.children(PoolRef())) == 1


def test_the_worker_id_is_still_a_child_of_dispatch():
    """Only the body moved to payload. The id has to stay computable."""
    node = Dispatch(body=RESIDENT, worker=Scratch.w)
    assert isinstance(nu.tree.children(node)[0], PoolRef)
    assert isinstance(nu.tree.children(node)[1], nustd.mem.ObjectRef)


def test_a_rewrite_carries_the_body_across_unchanged():
    """``_with_children`` shares the payload; a Nu term is immutable, so that is safe."""
    node = Dispatch(body=RESIDENT, worker=7)
    variant = node._with_children(*nu.tree.children(node))
    assert nu.tree.payload(variant)["body"] is RESIDENT
    assert nu.tree.payload(variant) is nu.tree.payload(node)


def test_no_walker_reaches_a_dispatched_body():
    """The documented consequence, asserted: the body is not in the tree."""
    tree = _provided(Dispatch(body=RESIDENT, worker=Scratch.w))
    program = nu.compile(tree)
    assert not any(t is RESIDENT for t in program.terms)
    assert not any(isinstance(t, nu.ForeverDo) for t in program.terms)
    # And it does not show in the render either.
    assert "ForeverDo" not in str(tree)
