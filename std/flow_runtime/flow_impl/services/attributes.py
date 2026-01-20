"""Service to managae local state of attributes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from pv.typing import EMPTY, Empty, Value, is_empty

from ..shapes import FlowState
from ._base import ServiceBase


if TYPE_CHECKING:
    from pv.storage import StorageContextType

    from every._abc import Context

    from ..types import Path


__all__ = ["AttributesService"]


@attrs.frozen
class AttributesService(ServiceBase):
    """Service to managae local state of attributes."""

    def set(
        self,
        path: Path,
        name: str,
        value: Value,
        *,
        storage_context: StorageContextType | None = None,
        step_name: str | None = None,
    ) -> None:
        """Set attribute with given name."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].attrs[name].set(value).execute(ctx)
            if step_name is not None:
                FlowState.attrs[step_name].aitems[name].set(value).execute(ctx)

    def get(
        self,
        path: Path,
        name: str,
        *,
        storage_context: StorageContextType | None = None,
        step_name: str | None = None,
    ) -> Value | Empty:
        """Check path and all ancestors for given attribute."""
        current = path

        with self.storage.context() as ctx:
            if step_name is not None:
                return FlowState.attrs[step_name].aitems[name].get().execute(ctx)

            while current is not None:
                val = self._get_single(current, name, ctx)

                if not is_empty(val):
                    return val

                if current.is_root:
                    break

                current = current.parent

            return EMPTY

    def remove(
        self,
        path: Path,
        name: str,
        *,
        storage_context: StorageContextType | None = None,
        step_name: str | None = None,
    ) -> None:
        """Remove attribute state for path."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].attrs[name].remove().execute(ctx)
            if step_name is not None:
                FlowState.attrs[step_name].aitems[name].remove().execute(ctx)

    def _get_single(
        self,
        path: Path,
        name: str,
        ctx: Context,
    ) -> Value | Empty:
        """Get value for given path (not ancestors)."""
        return FlowState.steps[path.to_key()].attrs[name].get().execute(ctx)
