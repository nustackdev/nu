"""Reactive protocols owned by Nu.

Nu defines the minimal contract that any reactive backend must satisfy to
plug into ``nu.core.reactive`` queries. Fabrics (virtuals, redis pubsub,
in-process, ...) match this protocol; Nu itself does not depend on any
concrete implementation.

Two protocols, both structural:

- ``ObserverProtocol`` -- process-scope reactive backend. Fabrics bind
  their observer instance under this type in ctx. Reactive queries
  resolve it via ``rt.ctx.fabrics.get(ObserverProtocol)`` and call
  ``subscribe(options)``.
- ``Subscription`` -- handle returned by ``subscribe``. The user binds
  receiver callbacks, unbinds them, and closes it when done. All three
  are required: ``React`` unbinds before it closes.

One marker, ``RESYNC``: a backend hands it to a receiver in place of a key
when it may have missed changes (a reconnect) and every subscriber should
re-read state. Level flows run a pass on it like on any wake. Event flows
skip it: it names no change for their body. Any other value, ``None``
included, is a real notification (a ui notify without payload is ``None``).

``options`` stays ``Any``: each backend defines its own filter dialect
and the corresponding view emits it (``view.on_change()`` etc.). Nu is a
pure conduit -- it never inspects options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "RESYNC",
    "ObserverProtocol",
    "Subscription",
]


class _Resync:
    """The type of ``RESYNC``. One instance, kept one across pickling."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "RESYNC"

    def __reduce__(self) -> str:
        # A global name: unpickling looks the module attribute back up, so a
        # marker sent to another process is still ``RESYNC`` by identity.
        return "RESYNC"


#: Handed to a receiver in place of a key: "you may have missed changes,
#: re-read state". Level flows run a pass on it, event flows skip it.
RESYNC: Any = _Resync()


@runtime_checkable
class Subscription(Protocol):
    """Handle returned by an observer. Bind and unbind receivers, close when done."""

    def bind(self, receiver: Callable[[Any], None]) -> None:
        """Bind a receiver callback to this subscription."""
        ...

    def unbind(self, receiver: Callable[[Any], None]) -> None:
        """Stop firing ``receiver``. Required, not optional: ``React`` calls it."""
        ...

    def close(self) -> None:
        """Close the subscription and release its registration."""
        ...


@runtime_checkable
class ObserverProtocol(Protocol):
    """Process-scope reactive backend. Fabrics bind under this type in ctx."""

    def subscribe(self, options: Any) -> Subscription:  # noqa: ANN401  (options is fabric-defined and opaque to nu)
        """Create a subscription for the given fabric-defined filter options."""
        ...
