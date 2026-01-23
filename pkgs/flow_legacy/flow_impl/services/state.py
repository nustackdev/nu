"""Cancellation service for flow execution control."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from ..shapes import FlowState
from ._base import ServiceBase


if TYPE_CHECKING:
    from pv.storage import StorageContextType

    from ..types import Path

__all__ = ["StateService"]


@attrs.frozen
class StateService(ServiceBase):
    """Service for managing flow state."""

    def init_flow_state(
        self,
        *,
        storage_context: StorageContextType | None = None,
    ) -> None:
        """Initialize flow state."""
        with self.storage.context() as ctx:
            FlowState.steps.store({}).execute(ctx)

    def init_flow_step_state(
        self,
        path: Path,
        *,
        storage_context: StorageContextType | None = None,
    ) -> None:
        """Initialize flow state for path."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].store(
                {
                    "cancellation": {
                        "cancelled": False,
                        "reason": "",
                        "timestamp": 0.0,
                    },
                    "checkpoint": {
                        "started": False,
                        "started_at": 0.0,
                        "finished": False,
                        "finished_at": 0.0,
                        "errored": False,
                        "error_message": "",
                        "errored_at": 0.0,
                    },
                    "attrs": {},
                }
            ).execute(ctx)
