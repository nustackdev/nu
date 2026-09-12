"""The law gate over ``nu.mp_pool`` trees. No processes: this is compile-time only."""

from __future__ import annotations

import pytest

import nu
from nu.lang.attributes import Cardinality, Sort
from nu.mp_pool import (
    Alive,
    Dispatch,
    Kill,
    Launch,
    PoolRef,
    Running,
    Teleport,
    WorkerPool,
    Workers,
)


RESIDENT = nu.ForeverDo(nu.DelayedDo(0.01, nu.SetCmd(nu.AttrRef("n"), 1)))


def _provided(body: nu.Nu) -> nu.Nu:
    return nu.Provide(WorkerPool, {"name": "laws"}, body)


TREES = {
    "launch": _provided(nu.SetCmd(nu.AttrRef("w"), Launch())),
    "launch_with_init": _provided(
        nu.SetCmd(nu.AttrRef("w"), Launch(init=nu.Provide(dict, {}))),
    ),
    "dispatch": _provided(Dispatch(body=RESIDENT, worker=nu.AttrRef("w"))),
    "dispatch_command_body": _provided(
        Dispatch(body=nu.SetCmd(nu.AttrRef("n"), 1), worker=nu.AttrRef("w")),
    ),
    "teleport_scalar": _provided(Teleport(body=nu.Add(1, 2), worker=nu.AttrRef("w"))),
    "teleport_command": _provided(
        Teleport(body=nu.SetCmd(nu.AttrRef("n"), 1), worker=nu.AttrRef("w")),
    ),
    "kill": _provided(Kill(worker=nu.AttrRef("w"))),
    "alive": _provided(nu.SetCmd(nu.AttrRef("a"), Alive(worker=nu.AttrRef("w")))),
    "running": _provided(nu.SetCmd(nu.AttrRef("r"), Running(worker=nu.AttrRef("w")))),
    "workers": _provided(nu.SetCmd(nu.AttrRef("ws"), nu.Collect(Workers()))),
    "explicit_pool_ref": _provided(
        nu.Let(
            "w",
            Launch(PoolRef()),
            Teleport(PoolRef(), body=nu.Add(1, 1), worker=nu.AttrRef("w")),
        ),
    ),
    "fluent": _provided(
        nu.Let(
            "w",
            PoolRef().launch(),
            nu.Sequential(
                PoolRef().dispatch(RESIDENT, nu.AttrRef("w")),
                PoolRef().teleport(nu.SetCmd(nu.AttrRef("n"), 1), nu.AttrRef("w")),
                PoolRef().kill(nu.AttrRef("w")),
            ),
        ),
    ),
    "fluent_reads": _provided(
        nu.Sequential(
            nu.SetCmd(nu.AttrRef("a"), PoolRef().alive(nu.AttrRef("w"))),
            nu.SetCmd(nu.AttrRef("r"), PoolRef().running(nu.AttrRef("w"))),
            nu.SetCmd(nu.AttrRef("ws"), nu.Collect(PoolRef().workers())),
        ),
    ),
    "dispatch_forever_body": _provided(
        Dispatch(body=nu.ForeverDo(nu.SetCmd(nu.AttrRef("n"), 1)), worker=nu.AttrRef("w")),
    ),
    "whole_lifecycle": _provided(
        nu.Let(
            "w",
            Launch(),
            nu.Sequential(
                Teleport(body=nu.SetCmd(nu.AttrRef("n"), 0), worker=nu.AttrRef("w")),
                Dispatch(body=RESIDENT, worker=nu.AttrRef("w")),
                Kill(worker=nu.AttrRef("w")),
            ),
        ),
    ),
}


@pytest.mark.parametrize("name", sorted(TREES))
def test_validate_passes(name):
    nu.validate(nu.compile(TREES[name]))


def test_dispatching_a_query_is_allowed():
    """A dispatched body's value is dropped by design, whatever it yields."""
    assert Dispatch(body=nu.Add(1, 2), worker=nu.AttrRef("w"))._payload["body"] is not None


def test_dispatching_a_non_nu_body_is_refused():
    with pytest.raises(TypeError, match="needs a Nu body"):
        Dispatch(body=42, worker=nu.AttrRef("w"))


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
        nu.ForeverDo(nu.SetCmd(nu.AttrRef("n"), 1)),
        nu.ReactForever(nu.AttrRef("n"), nu.SetCmd(nu.AttrRef("m"), 1)),
        nu.Sequential(nu.SetCmd(nu.AttrRef("n"), 1)),
        nu.SetCmd(nu.AttrRef("n"), 1),
    ],
)
def test_a_flow_body_is_accepted_and_the_tree_still_validates(body):
    """The whole point of the payload: a Flow body a Command could not hold."""
    node = Dispatch(body=body, worker=nu.AttrRef("w"))
    assert node._payload["body"] is body
    nu.validate(nu.compile(_provided(node)))


# --- the fluent interface ---------------------------------------------------


def _same_shape(a: nu.Nu, b: nu.Nu) -> bool:
    """Structural equality by class, payload and child shape, recursively."""
    return (
        type(a) is type(b)
        and a._payload == b._payload
        and len(a._children) == len(b._children)
        and all(_same_shape(x, y) for x, y in zip(a._children, b._children, strict=True))
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
    (lambda p: p.workers(), lambda p: Workers(p)),
]


@pytest.mark.parametrize(("fluent", "direct"), FLUENT)
def test_the_fluent_form_builds_the_same_term(fluent, direct):
    assert _same_shape(fluent(PoolRef()), direct(PoolRef()))


def test_the_fluent_form_puts_the_receiver_in_the_pool_slot():
    ref = PoolRef()
    assert ref.kill(7)._children[0] is ref
    assert ref.launch()._children[0] is ref
    assert ref.workers()._children[0] is ref
    # Teleport's pool slot is children[1]; the body is children[0] by Span rule.
    assert ref.teleport(RESIDENT, 7)._children[1] is ref


def test_the_fluent_dispatch_still_keeps_its_body_in_payload():
    assert PoolRef().dispatch(RESIDENT, 7)._payload["body"] is RESIDENT


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
        Workers(),
    ]
    for atom in atoms:
        assert 7 not in atom._payload.values()
        assert set(atom._payload) <= {"carry", "body"}
    # And the pool ref itself, unlike the tag nu.mp's MpWorkerRef used to hold.
    assert PoolRef()._payload == {}
    assert len(PoolRef()._children) == 1


def test_the_worker_id_is_still_a_child_of_dispatch():
    """Only the body moved to payload. The id has to stay computable."""
    node = Dispatch(body=RESIDENT, worker=nu.AttrRef("w"))
    assert isinstance(node._children[0], PoolRef)
    assert node._children[1] == nu.AttrRef("w") or isinstance(node._children[1], nu.AttrRef)


def test_a_rewrite_carries_the_body_across_unchanged():
    """``_with_children`` shares the payload; a Nu term is immutable, so that is safe."""
    node = Dispatch(body=RESIDENT, worker=7)
    variant = node._with_children(*node._children)
    assert variant._payload["body"] is RESIDENT
    assert variant._payload is node._payload


def test_no_walker_reaches_a_dispatched_body():
    """The documented consequence, asserted: the body is not in the tree."""
    tree = _provided(Dispatch(body=RESIDENT, worker=nu.AttrRef("w")))
    program = nu.compile(tree)
    assert RESIDENT not in program.terms
    assert not any(isinstance(t, nu.ForeverDo) for t in program.terms)
    # And it does not show in the render either.
    assert "ForeverDo" not in str(tree)
