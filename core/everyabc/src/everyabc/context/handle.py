"""Handle — scoped resource for execution.

Handles are runtime resources consumed by Terms during execution.
Examples: transactions, snapshots, connections, sessions.

Design:
    - Handles are created by infrastructure (substrates, factories)
    - Handles are scoped to Spans (opened/closed at boundaries)
    - Terms consume handles from Context
"""

from __future__ import annotations


__all__ = [
    "Handle",
]


class Handle:
    """Scoped resource handle. Consumed by Terms via Context.

    Handles represent runtime resources:
    - KV snapshot (read-only view)
    - KV transaction (read-write atomic access)
    - Network session (connection)
    - File handle, cursor, etc.

    Lifecycle:
    - Created by infrastructure (Substrate, factory, etc.)
    - Scoped to a Span boundary
    - Released when Span exits

    Subclass to add resource-specific methods.
    """

    def release(self) -> None:
        """Release this handle's resources.

        Called by executor when exiting a Span.
        Override to implement cleanup logic.
        """
