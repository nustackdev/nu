"""PV ref base mixin providing storage access.

PVRefMixin provides the core storage access pattern for PV refs.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from pv.loc import path
from pv.typing import Empty, Sentinel
from pv.typing.view import capabilities as view_capabilities

from every import Context, Ref, Term


if TYPE_CHECKING:
    from every import Shape

__all__ = [
    "PVPrimitiveRefMixin",
    "PVRefMixin",
    "PVViewRefMixin",
]


logger = getLogger(__name__)


class PVRefMixin[T]:
    """Base mixin for all PV refs.

    Provides common functionality for PV storage access.
    """

    address: path.PathAddress | Term
    parent_ref: Ref | None
    owner_shape: type[Shape] | None

    def get_root_shape(self) -> type[Shape] | None:
        """Get the root shape for context lookup."""
        if self.owner_shape is not None:
            return self.owner_shape
        if self.parent_ref is not None:
            return self.parent_ref.get_root_shape()
        return None


class PVPrimitiveRefMixin[T](PVRefMixin[T]):
    """Mixin providing get() for PV primitive refs.

    This mixin provides the PV-specific get() implementation that
    navigates through the view hierarchy to read values.
    """

    value_type: type[T]

    def resolve(self, context: Context) -> path.PathToValue:
        """Resolve to complete path ending at value.

        Args:
            context: Execution context

        Returns:
            Path ending with value segment
        """
        if isinstance(self.address, Term):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((address, self.value_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.value_type))

        logger.debug(
            "PVPrimitiveRefMixin resolved",
            extra={
                "address": address,
                "value_type": type(self.value_type).__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path  # type: ignore

    def get(self, ctx: Context) -> T | Sentinel:
        """Get the value from PV storage.

        Navigates through the view hierarchy and reads the value.
        Returns Empty if the value doesn't exist.
        """
        # Resolve ref to path
        value_path = self.resolve(ctx)

        # Get root view from context
        root_view = ctx.get_context_for_shape(self.get_root_shape()).root_view

        # Navigate to parent and get key
        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_capabilities.Subscriptable):
                return parent_view[key]
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return Empty()


class PVViewRefMixin[T, ViewT](PVRefMixin[T]):
    """Mixin providing view access for PV collection refs.

    This mixin provides the PV-specific implementation for collection
    refs that need to access views directly.
    """

    view_type: type[ViewT]

    def resolve(self, context: Context) -> path.PathToView:
        """Resolve to path ending at this shape's view.

        Args:
            context: Execution context

        Returns:
            Path ending with view segment
        """
        if isinstance(self.address, Term):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((address, self.view_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.view_type))

        logger.debug(
            "PVViewRefMixin resolved",
            extra={
                "address": address,
                "view_type": self.view_type.__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    def get_view(self, ctx: Context) -> ViewT:
        """Get the view instance from PV storage.

        Navigates through the view hierarchy to get this view.
        """
        view_path = self.resolve(ctx)
        root_view = ctx.get_context_for_shape(self.get_root_shape()).root_view

        if not view_path:
            return root_view  # type: ignore
        return path.navigate_view(root_view, view_path)  # type: ignore
