"""Bracket spans: the named lifecycle boundaries the core ships.

A Bracket is the lifecycle sub-shape of Span (sort BRACKET). It runs the body
inside a scope it opens before and tears down after, a snapshot to read
against, a transaction to commit or roll back. Transparent like every Span, it
forwards the body's yield unchanged (scalar, stream, or nothing).

``nu.Bracket`` is the base: its ``_open`` / ``_aopen`` are no-op context
managers, so a bare bracket just runs its body. The core ships two named
brackets on it, ``Snapshot`` and ``Transaction``, as the model-level shapes,
with that no-op lifecycle. A fabric subclasses them and overrides the
lifecycle to talk to a real store (see ``nustd.kv.interactions.atomicity``).

The lifecycle is one method, ``_open`` - a context manager. It opens the
boundary, yields the Context the body runs on with what it opened pushed on
top, then commits on a clean exit or rolls back on an exception:

    @contextmanager
    def _open(self, ctx, *config):
        txns = [...open...]                           # per-run handles, in the frame
        try:
            yield ctx.lazy(Txn, open_txn)             # body runs on this Context
        except BaseException:
            for t in txns: t.abort()                  # roll back, then re-raise
            raise
        else:
            for t in txns: t.commit()                 # commit

The per-run handles (the open snapshots, the open transactions) live in the
context manager's own frame, captured by closure - never on ``self``. A Term is
immutable and shared across every execution, so it can hold no per-run state
(see ``AUTHORING.md`` - "No per-run or cross-call state"). The Context is never
changed: what the scope provides is a frame on the Context it yields, gone
with the body. For a stream
body the scope spans the drain: it opens when the stream starts and closes
(commit / rollback) when it is exhausted, realizing the body's stream inside
the boundary.
"""

from __future__ import annotations

from nu.lang import Bracket


__all__ = ["Snapshot", "Transaction"]


class Snapshot(Bracket):
    """Read-only boundary around a body: snapshots its reads, nothing to commit.

    At the core level ``_open`` is a pass-through, so a bare
    ``Snapshot(body)`` runs the body unchanged. A fabric-aware Snapshot
    subclasses this and overrides ``_open`` to open a real read snapshot and
    close it after, giving the body a consistent view to read against.

    Args:
        body: the interaction to run inside the boundary.

    Yields:
        The body's own yield, unchanged. A core Snapshot adds no lifecycle
        of its own; only a fabric's override does.

    Example:
        >>> nu.run(nu.Snapshot(nu.Add(1, 2)))[0]
        3
    """


class Transaction(Bracket):
    """Atomic boundary around a body: commits on success, rolls back on failure.

    At the core level ``_open`` is a pass-through, so a bare
    ``Transaction(body)`` runs the body unchanged. A fabric-aware
    Transaction subclasses this and overrides ``_open`` to open a real
    write transaction, committing it on a clean exit and aborting it if the
    body raises.

    Args:
        body: the interaction to run inside the boundary.

    Yields:
        The body's own yield, unchanged. A core Transaction adds no
        lifecycle of its own; only a fabric's override does.

    Example:
        >>> nu.run(nu.Transaction(nu.Add(1, 2)))[0]
        3
    """
