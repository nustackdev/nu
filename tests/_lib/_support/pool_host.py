"""A host process running a ``WorkerPool``, for the tests that kill or signal the host.

Run as ``python -m _support.pool_host <mode>`` with ``tests/_lib`` on
``PYTHONPATH``. Every line it prints is one JSON object, so the test can read
its state while it runs.

Modes:

- ``kill``: three workers, one idle, one holding its loop in a sync sleep, one
  whose body started a ``sleep`` subprocess. Prints their pids and pgids and
  the subprocess's pid, then sleeps until killed. The test SIGKILLs it and
  checks nothing survives.
- ``sigint``: two workers, one spinning in a sync busy loop, one idle. Prints
  ``ready``, sleeps until a SIGINT lands on it, then reports whether the
  workers were left alone (the spin still running, the idle one answering),
  cleans up in order and exits 0.
- ``exit``: two workers, one holding its loop in a sync sleep, and no cleanup
  at all: the host just returns. Workers are not daemon processes, so without
  the pool's own atexit hook the interpreter would join them forever.
"""

from __future__ import annotations

import json
import os
import sys
import time

import nu
from _support.pool_workers import Block, Sleeper, Spin
from nustd.mp_pool import WorkerPool


def _say(**fields: object) -> None:
    sys.stdout.write(json.dumps(fields) + "\n")
    sys.stdout.flush()


def _kill_mode() -> None:
    pool = WorkerPool(name="host")
    pool.setup(None)
    idle = pool.launch()
    blocked = pool.launch()
    parent = pool.launch()
    pool.dispatch(blocked, Block(600))
    sleeper = pool.teleport(parent, Sleeper(600))
    _say(
        host=os.getpid(),
        workers=[[w, pool.status(w).pid, pool.status(w).pgid] for w in (idle, blocked, parent)],
        sleeper=sleeper,
    )
    time.sleep(600)


def _sigint_mode() -> None:
    pool = WorkerPool(name="host")
    pool.setup(None)
    spinning = pool.launch()
    idle = pool.launch()
    pool.dispatch(spinning, Spin(600))
    _say(ready=True, host=os.getpid(), pids=[pool.status(spinning).pid, pool.status(idle).pid])
    try:
        time.sleep(600)
    except KeyboardInterrupt:
        time.sleep(0.3)  # had the SIGINT reached the spinning worker, its body would be over
        _say(
            interrupted=True,
            spin_running=bool(pool.status(spinning).jobs),
            idle_answers=pool.teleport(idle, nu.Add(1, 2)),
        )
        pool.cleanup()
        _say(cleaned=True, workers=pool.workers())
        return
    _say(interrupted=False)


def _exit_mode() -> None:
    pool = WorkerPool(name="host")
    pool.setup(None)
    idle = pool.launch()
    blocked = pool.launch()
    pool.dispatch(blocked, Block(600))
    _say(host=os.getpid(), pids=[pool.status(idle).pid, pool.status(blocked).pid])
    # No cleanup: the pool is simply dropped on the floor at interpreter exit.


if __name__ == "__main__":
    {"kill": _kill_mode, "sigint": _sigint_mode, "exit": _exit_mode}[sys.argv[1]]()
