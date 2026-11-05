"""The law gate over ``nustd.mp_pool`` trees. No processes: this is compile-time only."""

from __future__ import annotations

import pytest

import nu
from nu.lang.attributes import Cardinality, Sort
from nu.lang.sentinels import UNSET
from nustd.mp_pool import (
    Cancel,
    Dispatch,
    Interrupt,
    Kill,
    Launch,
    PoolRef,
    Status,
    Stop,
    Teleport,
    Wait,
    WorkerPool,
    Workers,
    pool,
)


class Scratch(nu.Shape):
    """Where these trees put what they read, and the worker they address."""

    n = nu.mem.ObjectRef.slot()
    m = nu.mem.ObjectRef.slot()
    w = nu.mem.ObjectRef.slot()
    j = nu.mem.ObjectRef.slot()
    s = nu.mem.ObjectRef.slot()
    c = nu.mem.ObjectRef.slot()
    ws = nu.mem.ObjectRef.slot()


RESIDENT = nu.ForeverDo(nu.DelayedDo(0.01, Scratch.n.set(1)))


def _provided(body: nu.Nu) -> nu.Nu:
    return nu.Provide(WorkerPool, {"name": "laws"}, body)


TREES = {
    "launch": _provided(Scratch.w.set(Launch())),
    "launch_with_init": _provided(
        Scratch.w.set(Launch(init=nu.Provide(dict, {}))),
    ),
    "dispatch": _provided(Dispatch(body=RESIDENT, worker=Scratch.w)),
    "dispatch_job_id": _provided(Scratch.j.set(Dispatch(body=RESIDENT, worker=Scratch.w))),
    "dispatch_command_body": _provided(
        Dispatch(body=Scratch.n.set(1), worker=Scratch.w),
    ),
    "cancel": _provided(Cancel(worker=Scratch.w, job=Scratch.j)),
    "interrupt": _provided(Interrupt(worker=Scratch.w)),
    "stop": _provided(Scratch.s.set(Stop(worker=Scratch.w))),
    "stop_with_grace": _provided(Stop(worker=Scratch.w, grace=0.5)),
    "teleport_scalar": _provided(Teleport(body=nu.Add(1, 2), worker=Scratch.w)),
    "teleport_command": _provided(
        Teleport(body=Scratch.n.set(1), worker=Scratch.w),
    ),
    "kill": _provided(Kill(worker=Scratch.w)),
    "status": _provided(Scratch.s.set(Status(worker=Scratch.w))),
    "wait": _provided(Scratch.c.set(Wait(worker=Scratch.w))),
    "wait_with_timeout": _provided(Scratch.c.set(Wait(worker=Scratch.w, timeout=0.5))),
    "preset": pool(name="laws", spares=1, body=Scratch.w.set(Launch())),
    "tagged": pool(
        name="laws",
        tags=("a",),
        body=nu.mem.Frame(
            Scratch,
            PoolRef("a").stop(Scratch.w),
            w=PoolRef("a").launch(),
        ),
    ),
    "workers": _provided(Scratch.ws.set(nu.Collect(Workers()))),
    "explicit_pool_ref": _provided(
        nu.mem.Frame(
            Scratch,
            Teleport(PoolRef(), body=nu.Add(1, 1), worker=Scratch.w),
            w=Launch(PoolRef()),
        ),
    ),
    "fluent": _provided(
        nu.mem.Frame(
            Scratch,
            nu.Sequential(
                PoolRef().dispatch(RESIDENT, Scratch.w),
                PoolRef().teleport(Scratch.n.set(1), Scratch.w),
                PoolRef().cancel(Scratch.w, 0),
                PoolRef().interrupt(Scratch.w),
                PoolRef().stop(Scratch.w, 1.0),
                PoolRef().kill(Scratch.w),
            ),
            w=PoolRef().launch(),
        ),
    ),
    "fluent_reads": _provided(
        nu.Sequential(
            Scratch.s.set(PoolRef().status(Scratch.w)),
            Scratch.c.set(PoolRef().wait(Scratch.w, 0.1)),
            Scratch.ws.set(nu.Collect(PoolRef().workers())),
        ),
    ),
    "dispatch_forever_body": _provided(
        Dispatch(body=nu.ForeverDo(Scratch.n.set(1)), worker=Scratch.w),
    ),
    "whole_lifecycle": _provided(
        nu.mem.Frame(
            Scratch,
            nu.Sequential(
                Teleport(body=Scratch.n.set(0), worker=Scratch.w),
                Dispatch(body=RESIDENT, worker=Scratch.w),
                Interrupt(worker=Scratch.w),
                Stop(worker=Scratch.w),
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


@pytest.mark.parametrize(
    "tree",
    [
        lambda: Kill(nu.Literal(object()), 0),
        lambda: Cancel(nu.Literal(object()), 0, 1),
        lambda: Interrupt(nu.Literal(object()), 0),
    ],
)
def test_a_void_mutator_without_a_ref_in_its_mutation_slot_is_refused(tree):
    """``ref_slots``: a VOID mutator has to land its write through a Ref."""
    with pytest.raises(Exception, match="slot 0 must hold a Ref"):
        nu.validate(nu.compile(tree()))


# --- the sorts --------------------------------------------------------------


def test_dispatch_is_a_scalar_action_yielding_the_job_id():
    """It mutates the pool and yields the job id ``Cancel`` takes. Not a Flow either way."""
    node = Dispatch(body=RESIDENT, worker=7)
    assert isinstance(node, nu.lang.ScalarAction)
    assert not isinstance(node, nu.Flow)
    assert type(node)._attributes["sort"].value is Sort.SCALAR_ACTION
    assert type(node)._attributes["cardinality"].value is Cardinality.SCALAR
    assert type(node)._attributes["mutates"].value == frozenset({0})
    assert "param_slots" not in type(node).__dict__


@pytest.mark.parametrize(
    ("node", "sort", "mutates"),
    [
        (Launch(), Sort.SCALAR_ACTION, frozenset({0})),
        (Cancel(worker=7, job=1), Sort.SCALAR_COMMAND, frozenset({0})),
        (Interrupt(worker=7), Sort.SCALAR_COMMAND, frozenset({0})),
        (Stop(worker=7), Sort.SCALAR_ACTION, frozenset({0})),
        (Kill(worker=7), Sort.SCALAR_COMMAND, frozenset({0})),
        (Status(worker=7), Sort.SCALAR_QUERY, None),
        (Wait(worker=7), Sort.SCALAR_QUERY, None),
        (Workers(), Sort.STREAM_QUERY, None),
    ],
)
def test_each_verb_has_its_sort(node, sort, mutates):
    attributes = type(node)._attributes
    assert attributes["sort"].value is sort
    if mutates is not None:
        assert attributes["mutates"].value == mutates


@pytest.mark.parametrize(
    "body",
    [
        nu.ForeverDo(Scratch.n.set(1)),
        nu.ReactEvery(Scratch.n, Scratch.m.set(1)),
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
    (lambda p: p.cancel(7, 3), lambda p: Cancel(p, 7, 3)),
    (lambda p: p.interrupt(7), lambda p: Interrupt(p, 7)),
    (lambda p: p.stop(7), lambda p: Stop(p, 7)),
    (lambda p: p.stop(7, 2.0), lambda p: Stop(p, 7, 2.0)),
    (lambda p: p.kill(7), lambda p: Kill(p, 7)),
    (lambda p: p.status(7), lambda p: Status(p, 7)),
    (lambda p: p.wait(7), lambda p: Wait(p, 7)),
    (lambda p: p.wait(7, 0.5), lambda p: Wait(p, 7, 0.5)),
    (lambda p: p.workers(), lambda p: Workers(p)),
]


@pytest.mark.parametrize(("fluent", "direct"), FLUENT)
def test_the_fluent_form_builds_the_same_term(fluent, direct):
    assert _same_shape(fluent(PoolRef()), direct(PoolRef()))
    assert _same_shape(fluent(PoolRef("a")), direct(PoolRef("a")))


def test_the_fluent_form_puts_the_receiver_in_the_pool_slot():
    ref = PoolRef()
    assert nu.tree.children(ref.kill(7))[0] is ref
    assert nu.tree.children(ref.launch())[0] is ref
    assert nu.tree.children(ref.workers())[0] is ref
    assert nu.tree.children(ref.stop(7))[0] is ref
    assert nu.tree.children(ref.status(7))[0] is ref
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
        Cancel(worker=7, job=7),
        Interrupt(worker=7),
        Stop(worker=7, grace=7),
        Kill(worker=7),
        Status(worker=7),
        Wait(worker=7, timeout=7),
        Workers(),
    ]
    for atom in atoms:
        # A body is a term, and `==` on a term builds a comparison: skip them.
        assert 7 not in [v for v in nu.tree.payload(atom).values() if not isinstance(v, nu.Nu)]
        assert set(nu.tree.payload(atom)) <= {"carry", "body"}
    # The pool ref holds its tag, which is the address, not a caller value.
    assert nu.tree.payload(PoolRef()) == {"tag": UNSET}
    assert nu.tree.payload(PoolRef("a")) == {"tag": "a"}
    assert len(nu.tree.children(PoolRef())) == 1


def test_the_worker_id_is_still_a_child_of_dispatch():
    """Only the body moved to payload. The id has to stay computable."""
    node = Dispatch(body=RESIDENT, worker=Scratch.w)
    assert isinstance(nu.tree.children(node)[0], PoolRef)
    assert isinstance(nu.tree.children(node)[1], nu.mem.ObjectRef)


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
