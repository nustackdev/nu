"""Event flows: the body gets the key of a real change.

An event flow runs its body for a change: the body is handed the real key of
a real notification and nothing else wakes it. That makes it the right kind
for reacting to something that happened (a click, a message, a key that was
written) and the wrong kind for keeping state right, because delivery is best
effort: a subscription can miss a write made just after it opened, and a
backend may drop a message. Neither is made up for here. Every notification
reaches the body, ``None`` included (a ui notify without payload). A body that
reads state and puts it right, whatever changed, belongs in a level flow
(``nu.core.reactive.level``), which can afford re-checks precisely because it
ignores the key.

Every one is a ``Control`` flow: it drives a mutating body under query
parameters (a change subscription, a condition) and yields nothing, exactly
like ``WhileDo`` / ``ForeverDo``. A change notification is bridged into async
via ``asyncio.Queue``, so all of them require an async runtime and raise from
their sync ``_compile`` path.

A body that wants the key that changed is a lambda over it
(``lambda key: ...``): it runs once, at construction, with a ref to the key,
and the name it binds under is minted for it. A plain tree body binds nothing,
unless ``changed_key`` names where to put the key for it. ``ReactWhile``'s
condition is a binder slot the same way.

Two axes split the family. A wake either runs one more pass or restarts the
running body (``Latest``), and there is either one body for the flow or one
per key (``Each``): ``ReactEvery`` runs every key in order, ``ReactEach`` in
order per key with keys side by side, ``ReactLatest`` restarts its one body
on a newer key, ``ReactLatestEach`` restarts only that key's body.
``ReactOnce`` and ``ReactWhile`` end: after one change, or once a condition
turns false. An error a body raises ends the flow after the other running
bodies are cancelled and drained.

One module per flow: ``once`` (``ReactOnce``), ``while_`` (``ReactWhile``),
``every`` (``ReactEvery``), ``latest`` (``ReactLatest``), ``each``
(``ReactEach``), ``latest_each`` (``ReactLatestEach``).
"""

from .each import ReactEach
from .every import ReactEvery
from .latest import ReactLatest
from .latest_each import ReactLatestEach
from .once import ReactOnce
from .while_ import ReactWhile


__all__ = [
    "ReactEach",
    "ReactEvery",
    "ReactLatest",
    "ReactLatestEach",
    "ReactOnce",
    "ReactWhile",
]
