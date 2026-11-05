"""nustd.mp_pool: the pool of worker processes as one fabric.

nustd.mp is the fabric of ONE process, and its whole lifecycle is the bracket.
nustd.mp_pool is the fabric of the fleet: one pool(...) owns N workers, and the
interactions address them by id. Every id is a child, never payload, so it
can come from a Ref, a mem slot or any query.

The toolkit, every verb hanging off the pool ref:

    launch / workers              hand out a worker, list the live ones
    teleport / dispatch / cancel  run work: request/reply, or resident + job id
    interrupt / stop / kill       stop work, stop the worker politely, end it now
    status / wait                 the worker's record, alive or gone

The one thing that IS payload is a Dispatch body, because a Flow does not
compose in an Interaction's slots. That means the body is not part of the
tree: no walker, rewrite, analysis or render reaches it. Apply whatever
passes a body needs to the body itself, before the Dispatch is built.

Run me: python examples/mp_pool.py
"""

import nu
import nustd


POOL = nustd.mp_pool.PoolRef()


class Ticks(nu.Shape):
    """What the resident work counts, in a dict every worker comes up holding."""

    n = nu.IntRef.slot()


# Resident work: a tree that never terminates, so it must be dispatched
# rather than teleported -- nobody is ever going to wait for its value.
# Top-level so it survives the pickle into a spawned child.
TICKER = Ticks.n.set(0) >> nu.ForeverDo(nu.DelayedDo(0.05, Ticks.n.set(Ticks.n + 1)))


def status_line(label: str, worker: object) -> nu.Nu:
    """Print one worker's status record under ``label``."""
    return nu.Print(nu.STDOUT, label, POOL.status(worker))


# =========================================================================
# Stand a pool up, take a worker, dispatch resident work to it, read it
# while it runs, stop it politely. One tree, one run, reporting itself.
# =========================================================================


def demo() -> None:
    tree = nustd.mp_pool.pool(
        name="cells",  # ps shows each worker as nu:cells-{id}
        # Every worker comes up holding one Ticks dict, so the resident body
        # and the teleports that read it see the same one.
        init=nu.Provide(dict, {}, tag=Ticks),
        spares=1,  # one warm worker kept on a shelf for launches; it fills in the background
        grace=5.0,  # the whole budget for stopping a worker, and for the close
        # Launch yields the worker's id; let holds it for the rest.
        body=nu.let(
            POOL.launch(),
            lambda worker: nu.Sequential(
                nu.Print(nu.STDOUT, "worker id        :", worker),
                # Dispatch returns as soon as the child has the tree and yields
                # the job id, which Cancel would take. It never waits for the body.
                nu.Print(nu.STDOUT, "job id           :", POOL.dispatch(TICKER, worker)),
                # Meanwhile a teleport reads the same worker, and is answered while
                # the resident body is still running in it.
                nu.DelayedDo(
                    0.3, nu.Print(nu.STDOUT, "ticks after 0.3s :", POOL.teleport(Ticks.n, worker))
                ),
                status_line("while it runs    :", worker),
                # Stop: the stop frame cancels the resident body, the init
                # teardown runs, the worker exits 0. SIGINT, SIGTERM and
                # SIGKILL would follow within grace if it did not.
                nu.Print(nu.STDOUT, "after stop       :", POOL.stop(worker)),
                nu.Print(nu.STDOUT, "live workers     :", nu.Collect(POOL.workers())),
            ),
        ),
    )
    nu.run(tree)


if __name__ == "__main__":
    demo()
