"""Reactive protocols owned by Nu.

Nu defines the minimal contract that any reactive backend must satisfy to
plug into ``nu.core.reactive`` queries. Fabrics (virtuals, redis pubsub,
in-process, ...) match this protocol; Nu itself does not depend on any
concrete implementation.

Two protocols, both structural:

- ``ObserverProtocol`` -- process-scope reactive backend. Fabrics bind
  their observer instance under this type in ctx. Reactive queries
  resolve it via ``rt.ctx.get(ObserverProtocol)`` and call
  ``subscribe(options)``.
- ``Subscription`` -- handle returned by ``subscribe``. The user binds
  receiver callbacks and closes it when done.

``options`` stays ``Any``: each backend defines its own filter dialect
and the corresponding view emits it (``view.on_change()`` etc.). Nu is a
pure conduit -- it never inspects options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "ObserverProtocol",
    "Subscription",
]


@runtime_checkable
class Subscription(Protocol):
    """Handle returned by an observer. Bind receivers, close when done."""

    def bind(self, receiver: Callable[[Any], None]) -> None:
        """Bind a receiver callback to this subscription."""
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
