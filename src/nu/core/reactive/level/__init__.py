"""Level flows: the key is dropped, the body reads state and makes it right.

A level flow does not hand its body the change. The body reads the current
state and makes it right: start what should run, stop what should not, write
what is missing, or answer whether a condition holds yet. Run twice with
nothing changed in between, the second run finds nothing to do. That is the
whole contract, and it is what makes these flows robust: since a pass ignores
why it runs, the flow can run it on wakes no subscription delivered, and a
missed notification costs a delay instead of a wrong state.

Change delivery is at most once. A fresh subscription can miss writes for a
short while (writers learn about it with a delay), and a backend may drop a
message. So a level flow wakes:

- once right after its subscription is bound, so the first read follows the
  subscribe and a write made before it is always seen;
- on every notification;
- on re-checks measured from binding: one at each ``after`` offset (default
  0.1, 0.3 and 1.0 seconds, the window a fresh subscription is blind in),
  then every ``every`` seconds forever (default 30; ``None`` turns the
  standing re-check off). A missed notification is caught by the next one.

``after`` and ``every`` are child terms like any other argument: a literal
schedule is checked when the flow is built, a computed one when it is read.

Wakes merge: whatever lands while a pass runs, one notification or a hundred,
is one more pass, which reads the state as it then is. The subscription is
held for the flow's whole life and never reopened.

Which kind to reach for: a body that reacts to what happened (a click, a
message, the key that was written) is an event body and belongs in the
``React*`` family, which hands it the real key and never invents a wake. A
body that keeps something in step with state, or waits for state to reach a
point, is a level body and belongs here.

Two axes split the family. A wake either runs one more pass of the body or
aligns arms that keep running until their id leaves the read (``Latest``),
and there is either one body or one per id (``Each``): ``Reconcile`` runs a
pass, ``ReconcileEach`` a pass per element, ``ReconcileLatest`` holds one arm
for the one id it reads, ``ReconcileLatestEach`` one arm per id. Ids are read
from state, never taken from notifications. An arm runs once per appearance
of its id: a finished arm stays finished until its id leaves a read and
comes back. ``WaitUntil`` returns once its condition reads true,
``ReconcileWhile`` once its condition reads false. An error a body raises ends the flow after the other
running arms are cancelled and drained.

Async-only, like the whole reactive set: the sync ``_compile`` path raises.

One module per flow: ``wait`` (``WaitUntil``), ``while_``
(``ReconcileWhile``), ``reconcile`` (``Reconcile``), ``each``
(``ReconcileEach``), ``latest`` (``ReconcileLatest``), ``latest_each``
(``ReconcileLatestEach``), and the private ``_wakes`` they share.
"""

from .each import ReconcileEach
from .latest import ReconcileLatest
from .latest_each import ReconcileLatestEach
from .reconcile import Reconcile
from .wait import WaitUntil
from .while_ import ReconcileWhile


__all__ = [
    "Reconcile",
    "ReconcileEach",
    "ReconcileLatest",
    "ReconcileLatestEach",
    "ReconcileWhile",
    "WaitUntil",
]
