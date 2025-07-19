"""
Context managers for snapshot handling in the tree package.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

import attrs

from ..backend import BackendProtocol, SnapshotProtocol
from ..types import TransactionalT

__all__ = [
    "SnapshotContext",
    "with_snapshot",
    "create_snapshot_context",
]


class SnapshotContext:
    """
    Context manager for conditional snapshot handling.

    If a snapshot is provided, uses that snapshot with no additional
    management (noop pattern). If no snapshot is provided, creates a new
    snapshot and manages its lifecycle (cleanup on exit).

    Args:
        backend: The backend to create snapshots from
        snap: Optional existing snapshot. If None, a new snapshot is created

    Example:
        ```python
        # With existing snapshot (noop - no cleanup)
        existing_snap = backend.begin_snapshot()
        with SnapshotContext(backend, existing_snap) as snap:
            value = snap.get(key)
        # existing_snap is still valid after context

        # Without existing snapshot (managed - auto cleanup)
        with SnapshotContext(backend) as snap:
            value = snap.get(key)
        # snapshot is automatically cleaned up
        ```
    """

    def __init__(
        self,
        backend: BackendProtocol,
        snap: Optional[SnapshotProtocol] = None,
    ):
        """
        Initialize snapshot context.

        Args:
            backend: Backend to create snapshots from
            snap: Optional existing snapshot
        """
        self.backend = backend
        self.provided_snap = snap
        self.managed_snap: Optional[SnapshotProtocol] = None

    def __enter__(self) -> SnapshotProtocol:
        """
        Enter snapshot context.

        Returns:
            Snapshot to use (either provided or newly created)
        """
        if self.provided_snap is not None:
            # Use provided snapshot (noop pattern)
            return self.provided_snap
        else:
            # Create and manage new snapshot
            self.managed_snap = self.backend.begin_snapshot()
            return self.managed_snap

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit snapshot context.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.managed_snap is not None:
            # Clean up managed snapshot
            self.managed_snap.close()


def create_snapshot_context(
    backend: BackendProtocol, snap: Optional[SnapshotProtocol] = None
) -> SnapshotContext:
    """
    Create a snapshot context for the given backend and optional snapshot.

    Args:
        backend: Backend to create snapshots from
        snap: Optional existing snapshot

    Returns:
        SnapshotContext for use in with statements

    Example:
        ```python
        # Used internally by State.with_dict_view(snapshot=True)
        def with_dict_view(self, *, snapshot: bool = False):
            if snapshot:
                snap_ctx = create_snapshot_context(self.backend, self.snap)
                with snap_ctx as snap:
                    return DictView(backend=self.backend, path=self.path, snap=snap)
            else:
                # Regular transaction-based view
                return create_view_context_manager(DictView, ...)
        ```
    """
    return SnapshotContext(backend, snap)


@contextmanager
def with_snapshot(obj: TransactionalT) -> Generator[TransactionalT, None, None]:
    """
    Context manager that provides snapshot context for an object.

    Args:
        obj: Object that has backend and snap attributes

    Yields:
        Object with snapshot context

    Example:
        ```python
        view = DictView(backend=backend, path=path, snap=None)
        with with_snapshot(view) as snap_view:
            value = snap_view.get(key)
        ```
    """
    snap_ctx = create_snapshot_context(obj.backend, obj.snap)
    with snap_ctx as snap:
        yield attrs.evolve(obj, snap=snap)
