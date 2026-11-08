"""``atomic``: one bracket per store a term touches, found from its refs.

Two root Shapes stand for two stores (``Space``, ``State``), each bound to its
own storage under its own tag, the way nuspace binds its files. Checks:

- a write gets a Transaction on its store, retried on conflict; a store only
  read gets a Snapshot; a read-only term gets Snapshots only.
- a key read from another store inside a write comes from that store's
  snapshot, and nothing else of that store is bracketed.
- a term writing two stores raises at build.
- all writes of a term land together or none do.
- nesting: an atomic term inside another is kept; an inner write bracket on
  another store stays its own commit; one on the written store raises.
- flows: atomic brackets a whole flow once, where auto_flow_atomic brackets
  each branch, and the two compose.
- mem refs never count, and a term with no store refs is left as is.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu import Context, Shape, arun, run
from nu.lang import ScalarQuery, is_null
from nustd.kv import (
    BracketError,
    DictRef,
    IntRef,
    NullAddressError,
    RetryOnConflict,
    Snapshot,
    Transaction,
    atomic,
    auto_flow_atomic,
    sqlite_navigator,
)
from virtuals import Navigator
from virtuals.codecs import NoOpCodec
from virtuals.storages.mem import InMemoryStorage
from virtuals.tkv.storage import (
    SnapshotProtocol,
    StorageTransactionConflictError,
    TransactionProtocol,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu.lang.runtime import Runtime


class Rec(Shape):
    value = IntRef.slot()


class Space(Shape):
    cell_keys = DictRef.slot(str)
    n = IntRef.slot()


class State(Shape):
    cells = DictRef.slot(Rec)
    m = IntRef.slot()
    log = DictRef.slot(int)


@pytest.fixture
def ctx() -> Iterator[Context]:
    """Space and State, each on its own in-memory storage under its own tag."""
    with InMemoryStorage(codec=NoOpCodec()) as space, InMemoryStorage(codec=NoOpCodec()) as state:
        yield (
            Context()
            .bind(Navigator, Navigator(space), Space)
            .bind(Navigator, Navigator(state), State)
        )


def _sig(term: object) -> str:
    """The bracket structure of a term, eg ``Retry[Transaction(State)[SetCmd]]``."""
    if isinstance(term, (Snapshot, Transaction)):
        scope = getattr(term.scope, "__name__", term.scope)
        return f"{type(term).__name__}({scope})[{_sig(nu.tree.children(term)[0])}]"
    if isinstance(term, RetryOnConflict):
        return f"Retry[{_sig(nu.tree.children(term)[0])}]"
    return type(term).__name__


class _Probe(ScalarQuery):
    """Runs ``fn(rt)`` and yields True; a stand-in for any read inside a bracket."""

    def __init__(self, fn: Callable[[Runtime], None]) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple) -> Callable:
        fn = self._payload["fn"]

        def thunk(rt: Runtime) -> bool:
            fn(rt)
            return True

        return thunk

    def _acompile(self, nid: int, children: tuple) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> bool:
            fn(rt)
            return True

        return athunk


def _bound(seen: dict) -> _Probe:
    """Record which store brackets the body sees."""

    def fn(rt: Runtime) -> None:
        fabrics = rt.ctx.fabrics
        for store in (Space, State):
            seen[store.__name__] = (
                "tx"
                if fabrics.has(TransactionProtocol, store)
                else "snap"
                if fabrics.has(SnapshotProtocol, store)
                else None
            )

    return _Probe(fn)


# --- structure: which brackets land -------------------------------------------


def test_a_write_gets_a_retried_transaction_on_its_store() -> None:
    assert _sig(atomic(State.m.set(1))) == "Retry[Transaction(State)[SetCmd]]"


def test_a_read_gets_a_snapshot_and_no_retry() -> None:
    assert _sig(atomic(State.m)) == "Snapshot(State)[IntRef]"


def test_a_key_from_another_store_reads_from_its_snapshot() -> None:
    term = atomic(State.cells[Space.cell_keys["k"]].value.set(1))
    assert _sig(term) == "Retry[Transaction(State)[Snapshot(Space)[SetCmd]]]"


def test_two_stores_read_get_a_snapshot_each() -> None:
    term = atomic(State.cells[Space.cell_keys["k"]].value)
    assert _sig(term) == "Snapshot(Space)[Snapshot(State)[IntRef]]"


def test_a_value_from_another_store_is_a_read() -> None:
    assert _sig(atomic(State.m.set(Space.n))) == (
        "Retry[Transaction(State)[Snapshot(Space)[SetCmd]]]"
    )


def test_a_term_writing_two_stores_raises_at_build() -> None:
    with pytest.raises(BracketError, match=r"writes 2 stores \(State, Space\)"):
        atomic(State.m.set(1) >> Space.n.set(2))


def test_a_term_writing_two_stores_in_flows_raises_too() -> None:
    with pytest.raises(BracketError):
        atomic(nu.IfDo(State.m.exists(), Space.n.set(1), State.m.set(1)))


def test_mem_writes_do_not_count() -> None:
    term = atomic(nu.let(State.m, lambda v: v.set(1)))
    assert isinstance(term, Snapshot)
    assert term.scope is State


def test_a_term_without_store_refs_is_left_as_is() -> None:
    term = nu.Noop()
    assert atomic(term) is term


# --- running it ---------------------------------------------------------------


def test_a_write_lands_in_its_own_store(ctx) -> None:
    run(atomic(Space.cell_keys["k"].set("c1")), ctx)
    run(atomic(State.cells[Space.cell_keys["k"]].value.set(5)), ctx)
    assert run(atomic(State.cells["c1"].value), ctx)[0] == 5
    assert run(atomic(State.cells[Space.cell_keys["k"]].value), ctx)[0] == 5
    assert run(atomic(Space.n.exists()), ctx)[0] is False


def test_only_the_touched_stores_are_bracketed(ctx) -> None:
    seen: dict = {}
    run(atomic(nu.let(_bound(seen), lambda _: State.m.set(1))), ctx)
    assert seen == {"Space": None, "State": "tx"}
    run(atomic(nu.let(_bound(seen), lambda _: State.m.set(Space.n.fallback(0)))), ctx)
    assert seen == {"Space": "snap", "State": "tx"}
    run(atomic(nu.let(_bound(seen), lambda _: State.m)), ctx)
    assert seen == {"Space": None, "State": "snap"}


def test_all_writes_land_together_or_none(ctx) -> None:
    writes = State.m.set(1) >> State.log["a"].set(2)
    with pytest.raises(ValueError, match="boom"):
        run(atomic(writes >> nu.raise_(ValueError, "boom")), ctx)
    assert run(atomic(State.m.exists().or_(State.log.exists())), ctx)[0] is False
    run(atomic(writes), ctx)
    assert run(atomic(State.log["a"]), ctx)[0] == 2


def test_a_lost_commit_is_retried(ctx) -> None:
    attempts: list[int] = []

    def lose_once(rt: Runtime) -> None:
        attempts.append(1)
        if len(attempts) == 1:
            raise StorageTransactionConflictError("lost the commit")

    run(atomic(nu.let(_Probe(lose_once), lambda _: State.m.set(3))), ctx)
    assert len(attempts) == 2
    assert run(atomic(State.m), ctx)[0] == 3


def test_the_last_conflict_is_raised(ctx) -> None:
    def always_lose(rt: Runtime) -> None:
        raise StorageTransactionConflictError("lost the commit")

    with pytest.raises(StorageTransactionConflictError):
        run(atomic(nu.let(_Probe(always_lose), lambda _: State.m.set(3))), ctx)
    assert run(atomic(State.m.exists()), ctx)[0] is False


def test_a_key_that_finds_nothing_aborts_the_write(ctx) -> None:
    with pytest.raises(NullAddressError):
        run(atomic(State.m.set(1) >> State.cells[Space.cell_keys["gone"]].value.set(1)), ctx)
    assert run(atomic(State.m.exists()), ctx)[0] is False


def test_the_async_path_answers_the_same(ctx) -> None:
    async def go() -> None:
        await arun(atomic(Space.cell_keys["k"].set("c1")), ctx)
        await arun(atomic(State.cells[Space.cell_keys["k"]].value.set(4)), ctx)
        assert (await arun(atomic(State.cells["c1"].value), ctx))[0] == 4

    asyncio.run(go())


def test_a_state_write_leaves_the_space_writer_free(tmp_path) -> None:
    # sqlite waits for a writer slot on async; a State-only write must not
    # hold Space's, so a Space write lands while the State one is still open
    def stores(body: nu.Nu) -> nu.Nu:
        return nu.With(
            sqlite_navigator(str(tmp_path / "space.db"), tags=(Space,)),
            sqlite_navigator(str(tmp_path / "state.db"), tags=(State,)),
            body=body,
        )

    held = atomic(State.m.set(1) >> nu.Delay(0.4) >> State.m.set(2))
    other = nu.Delay(0.05) >> nu.Timeout(0.2, atomic(Space.n.set(1)))
    asyncio.run(arun(stores(nu.ParallelAsync(held, other)), max_parallel=2))
    assert run(stores(atomic(Space.n)))[0] == 1
    assert run(stores(atomic(State.m)))[0] == 2


# --- nesting ------------------------------------------------------------------


def test_atomic_of_an_atomic_term_is_that_term() -> None:
    once = atomic(State.m.set(1))
    assert atomic(once) is once
    read = atomic(State.cells[Space.cell_keys["k"]].value)
    assert atomic(read) is read


def test_an_inner_write_on_another_store_stays_its_own_commit(ctx) -> None:
    term = atomic(atomic(Space.n.set(1)) >> State.m.set(2))
    assert _sig(term) == "Retry[Transaction(State)[Sequential]]"
    run(term, ctx)
    assert run(atomic(Space.n), ctx)[0] == 1
    assert run(atomic(State.m), ctx)[0] == 2


def test_an_inner_write_bracket_on_the_written_store_raises() -> None:
    with pytest.raises(BracketError, match="never join"):
        atomic(atomic(State.m.set(1)) >> State.log["a"].set(2))
    with pytest.raises(BracketError):
        atomic(Transaction(State.m.set(1), scope=State) >> State.log["a"].set(2))


def test_an_inner_untagged_write_bracket_raises() -> None:
    with pytest.raises(BracketError):
        atomic(Transaction(Space.n.set(1)) >> State.m.set(2))


def test_an_inner_read_bracket_reads_through_the_write(ctx) -> None:
    inner = Snapshot(State.m, scope=State)
    run(atomic(State.m.set(7) >> nu.let(inner, lambda v: State.log["seen"].set(v))), ctx)
    assert run(atomic(State.log["seen"]), ctx)[0] == 7


# --- flows ----------------------------------------------------------------------


def _count(term: object, cls: type) -> int:
    found = isinstance(term, cls)
    return found + sum(_count(c, cls) for c in nu.tree.children(term))


def test_a_flow_gets_one_bracket_around_all_of_it() -> None:
    flow = State.m.set(1) >> nu.ForEachDo(nu.List(["a", "b"]), lambda k: State.log[k].set(1))
    assert _count(atomic(flow), Transaction) == 1
    assert _count(auto_flow_atomic(flow), Transaction) == 2


def test_a_flow_commits_once(ctx) -> None:
    flow = nu.ForEachDo(nu.List(["a", "b", "c"]), lambda k: State.log[k].set(1))
    with pytest.raises(ValueError, match="boom"):
        run(atomic(flow >> nu.raise_(ValueError, "boom")), ctx)
    assert run(atomic(State.log.exists()), ctx)[0] is False
    run(atomic(nu.IfDo(Space.n.exists().not_(), flow)), ctx)
    assert run(atomic(State.log["c"]), ctx)[0] == 1


def test_auto_flow_atomic_keeps_an_atomic_branch() -> None:
    branch = atomic(State.m.set(1))
    wrapped = auto_flow_atomic(branch >> Space.n.set(2))
    first, second = nu.tree.children(wrapped)
    assert first is branch
    assert isinstance(second, Transaction)


def test_atomic_over_auto_flow_atomic_adds_nothing() -> None:
    flow = auto_flow_atomic(State.m.set(1) >> Space.n.set(2))
    assert atomic(flow) is flow


def test_a_read_only_null_check_stays_a_read(ctx) -> None:
    assert is_null(run(atomic(State.cells[Space.cell_keys["gone"]].value), ctx)[0])
