"""Cancellation service for flow execution control."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import attrs

from everyflow.exceptions import CancelledError

from ..shapes import FlowState
from ._base import ServiceBase


if TYPE_CHECKING:
    from everyterm.term import Context, Empty

    from ..types import Path


__all__ = ["CancellationService"]


@attrs.frozen
class CancellationService(ServiceBase):
    """Service for managing flow cancellation state."""

    def cancel(
        self,
        path: Path,
        reason: str = "manual",
    ) -> None:
        """Set cancellation for path."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].cancellation.cancelled.set(True).execute(ctx)
            FlowState.steps[path.to_key()].cancellation.reason.set(reason).execute(ctx)
            FlowState.steps[path.to_key()].cancellation.timestamp.set(time.time()).execute(ctx)
            FlowState.steps[path.to_key()].cancellation.path.set(path.to_key()).execute(ctx)

    def terminate_cancelled(
        self,
        path: Path,
    ) -> None:
        """Raise cancellation exception if flow has been cancelled."""
        if self.is_cancelled(path):
            raise CancelledError()

    def is_cancelled(
        self,
        path: Path,
    ) -> bool:
        """Check path and all ancestors for cancellation."""
        current = path

        with self.storage.context() as ctx:
            while current is not None:
                if self._check_single(current, ctx):
                    return True

                if current.is_root:
                    break

                current = current.parent

        return False

    def clear(
        self,
        path: Path,
    ) -> None:
        """Clear cancellation state for path."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].cancellation.cancelled.set(False).execute(ctx)
            FlowState.steps[path.to_key()].cancellation.reason.set("").execute(ctx)
            FlowState.steps[path.to_key()].cancellation.timestamp.set(0.0).execute(ctx)

    def get_reason(
        self,
        path: Path,
    ) -> str | Empty:
        """Get cancellation reason for path."""
        with self.storage.context() as ctx:
            return FlowState.steps[path.to_key()].cancellation.reason.get().execute(ctx)

    def _check_single(
        self,
        path: Path,
        ctx: Context,
    ) -> bool:
        """Check single path (not ancestors)."""
        result = FlowState.steps[path.to_key()].cancellation.cancelled.get().execute(ctx)
        return bool(result)
