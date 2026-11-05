"""nu.core.reactive -- reactivity standard and the flows that consume it.

Owns the reactive contract (``ObserverProtocol`` + ``Subscription``), the
interaction atoms that open subscriptions (``OnChange`` / ``OnChildChange`` /
``OnChildrenChange`` / ``OnDescendantsChange`` / ``OnPrimitiveChange``), and
the flows that run bodies against them, in two kinds:

- **event** (``React``, ``ReactWhile``, ``ReactForever``, ``ReactLatest``):
  the body is handed the real key of a real notification and runs on real
  notifications only. Best effort, since delivery is at most once. For
  reacting to what happened.
- **level** (``ReconcileReactive``, ``WaitReactive``, ``ForEachParReactive``): the
  body gets no key; it reads the current state and makes it right. Because it
  ignores what changed, the flow also wakes it right after subscribing and on
  a re-check schedule, so a missed notification is late, never lost. For
  keeping state in step and waiting for state.

``Stream`` drains an ordered collection and then follows it.

Modules: ``protocol`` (the contract), ``interactions`` (the ``On*`` atoms),
``event`` and ``level`` (the two kinds), ``stream``, and the private
``_wakes`` the level flows share.

Nu defines the standard; fabrics (nustd.kv, and any future backend) bind
their observer under ``ObserverProtocol`` in ctx and match its structural
shape. Nu never depends on a concrete reactive backend.
"""

from nu.core.reactive.event import React, ReactForever, ReactLatest, ReactWhile
from nu.core.reactive.interactions import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)
from nu.core.reactive.level import ForEachParReactive, ReconcileReactive, WaitReactive
from nu.core.reactive.protocol import ObserverProtocol, Subscription
from nu.core.reactive.stream import Stream


__all__ = [
    "ForEachParReactive",
    "ObserverProtocol",
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
    "React",
    "ReactForever",
    "ReactLatest",
    "ReactWhile",
    "ReconcileReactive",
    "Stream",
    "Subscription",
    "WaitReactive",
]
