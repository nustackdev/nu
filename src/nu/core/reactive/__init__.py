"""nu.core.reactive: the reactivity standard and the flows that consume it.

Owns the reactive contract (``ObserverProtocol`` + ``Subscription``), the
sources that open subscriptions (``OnChange`` / ``OnChildChange`` /
``OnChildrenChange`` / ``OnDescendantsChange`` / ``OnPrimitiveChange``, and
``OnAny`` over several), and the flows that run bodies against them, in two
triggers:

- **event** (``ReactOnce``, ``ReactWhile``, ``ReactEvery``, ``ReactLatest``,
  ``ReactEach``, ``ReactLatestEach``): the body is handed the real key of a
  real notification and runs on real notifications only. Best effort, since
  delivery is at most once. For reacting to what happened.
- **level** (``WaitUntil``, ``ReconcileWhile``, ``Reconcile``,
  ``ReconcileEach``, ``ReconcileLatest``, ``ReconcileLatestEach``): the body
  gets no key; it reads the current state and makes it right. Because it
  ignores what changed, the flow also wakes it right after subscribing and on
  a re-check schedule, so a missed notification is late, never lost. For
  keeping state in step and waiting for state.

Inside each trigger there are two axes: what a wake does to a running body
(run one more pass, or restart it) and how many bodies run (one, or one per
key or id). Names follow that grid: the family (``React*`` event,
``Reconcile*`` and ``WaitUntil`` level, ``On*`` a source), then ``Latest``
when a newer wake restarts a running body, ``Each`` when there is one body
per key or id::

                 event one      event many        level one         level many
    pass         ReactEvery     ReactEach         Reconcile         ReconcileEach
    restart      ReactLatest    ReactLatestEach   ReconcileLatest   ReconcileLatestEach
    wait / end   ReactOnce      -                 WaitUntil         -
                 ReactWhile                       ReconcileWhile

Every flow lets an unhandled error out: an arm that raises cancels and
drains its siblings, closes the subscription and re-raises. Isolation and
supervision are composed with ``TryCatch`` and ``Retry``.

``Stream`` (the cursor kind) drains an ordered collection and then follows
it, once per item.

Layout: ``protocol`` (the contract), ``sources/`` (the ``On*`` queries),
``event/`` and ``level/`` (one module per flow), ``cursor/`` (``Stream``),
and the private ``_body`` (running a body, binding the changed key) and
``_arms`` (the arm book of the per-id flows).

Nu defines the standard; fabrics (nustd.kv, and any future backend) bind
their observer under ``ObserverProtocol`` in ctx and match its structural
shape. Nu never depends on a concrete reactive backend.
"""

from nu.core.reactive.cursor import Stream
from nu.core.reactive.event import (
    ReactEach,
    ReactEvery,
    ReactLatest,
    ReactLatestEach,
    ReactOnce,
    ReactWhile,
)
from nu.core.reactive.level import (
    Reconcile,
    ReconcileEach,
    ReconcileLatest,
    ReconcileLatestEach,
    ReconcileWhile,
    WaitUntil,
)
from nu.core.reactive.protocol import ObserverProtocol, Subscription
from nu.core.reactive.sources import (
    OnAny,
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)


__all__ = [
    "ObserverProtocol",
    "OnAny",
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
    "ReactEach",
    "ReactEvery",
    "ReactLatest",
    "ReactLatestEach",
    "ReactOnce",
    "ReactWhile",
    "Reconcile",
    "ReconcileEach",
    "ReconcileLatest",
    "ReconcileLatestEach",
    "ReconcileWhile",
    "Stream",
    "Subscription",
    "WaitUntil",
]
