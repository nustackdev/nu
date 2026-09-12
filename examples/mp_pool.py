"""nu.mp_pool: the pool of worker processes as one fabric.

nu.mp is the fabric of ONE process, and its whole lifecycle is the bracket.
nu.mp_pool is the fabric of the fleet: one Provide owns N workers, and the
interactions address them by id. Every id is a child, never payload, so it
can come from a Ref, an AttrRef or any query.

The one thing that IS payload is a Dispatch body, because a Command cannot
hold a Flow in a child slot. That means the body is not part of the tree:
no walker, rewrite, analysis or render reaches it. Apply whatever passes a
body needs to the body itself, before the Dispatch is built.

Run me: python examples/mp_pool.py
"""

import nu
from nu.core.io import STDOUT
from nu.mp_pool import PoolRef, WorkerPool


POOL = PoolRef()
WORKER = nu.AttrRef("w")

# Resident work: a tree that never terminates, so it must be dispatched
# rather than teleported -- nobody is ever going to wait for its value.
# Top-level so it survives the pickle into a spawned child.
TICKER = nu.Sequential(
    nu.SetCmd(nu.AttrRef("tick"), 0),
    nu.ForeverDo(nu.DelayedDo(0.05, nu.SetCmd(nu.AttrRef("tick"), nu.Add(nu.AttrRef("tick"), 1)))),
)
READ = nu.AttrRef("tick")


# =========================================================================
# Launch a worker, dispatch resident work to it, watch it run, kill it.
# One tree, one run, reporting itself. Every verb hangs off the pool ref.
# =========================================================================


def demo() -> None:
    tree = nu.Provide(
        WorkerPool,
        {"name": "nu"},
        nu.Sequential(
            # Launch yields the new worker's id; bind it and address everything by it.
            nu.SetCmd(WORKER, POOL.launch()),
            nu.Print(STDOUT, "worker id        :", WORKER),
            # Dispatch returns as soon as the child has the tree. It does not wait,
            # which is the whole reason resident work is possible at all.
            POOL.dispatch(TICKER, WORKER),
            # Meanwhile a teleport reads the same worker, and is answered while
            # the resident body is still running in it.
            nu.DelayedDo(0.3, nu.Print(STDOUT, "ticks after 0.3s :", POOL.teleport(READ, WORKER))),
            nu.DelayedDo(0.3, nu.Print(STDOUT, "ticks after 0.6s :", POOL.teleport(READ, WORKER))),
            # A real kill: terminate and reap. No cooperative stop sentinel,
            # because a worker busy with a resident body never reads its pipe.
            POOL.kill(WORKER),
            nu.Print(STDOUT, "alive after kill :", POOL.alive(WORKER)),
        ),
    )
    nu.run(tree)


if __name__ == "__main__":
    demo()
