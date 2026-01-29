"""Observable capability bases for LValue references.

This module provides observation-related capability bases:
- PrimitiveObservableBase - for primitive value observation
- ViewObservableBase - for container observation
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pv.loc import key

    from every_pv.morphisms import (
        OnChangeOp,
        OnChildChangeOp,
        OnChildrenChangeOp,
        OnDescendantsChangeOp,
        OnPrimitiveChangeOp,
    )
    from everyabc import Sentinel, Term


__all__ = [
    "PrimitiveObservableBase",
    "ViewObservableBase",
]


# =============================================================================
# OBSERVABLE CAPABILITY BASES
# =============================================================================


class PrimitiveObservableBase:
    """Implementation base for primitive value observation.

    Implements observation for leaf values via parent view's ChildObservable.
    """

    def on_change(self) -> OnPrimitiveChangeOp:
        """Create change subscription operation for this value.

        Returns:
            OnPrimitiveChangeOp that creates subscription when executed

        Example:
            >>> Once(User.name.on_change(), HandleNameChange())
        """
        from every_pv.morphisms import OnPrimitiveChangeOp

        return OnPrimitiveChangeOp(self)


class ViewObservableBase:
    """Implementation base for container observation.

    Implements observation for containers via Observable and ChildObservable protocols.
    """

    def on_change(self) -> OnChangeOp:
        """Subscribe to all changes in this view.

        Returns:
            OnChangeOp that creates subscription when executed

        Example:
            >>> OnChange(User.profile.on_change(), SyncProfile())
        """
        from every_pv.morphisms import OnChangeOp

        return OnChangeOp(self)

    def on_child_change(self, address: str | Sentinel | Term[str | Sentinel]) -> OnChildChangeOp:
        """Subscribe to changes on a specific child.

        Args:
            address: Child address to watch

        Returns:
            OnChildChangeOp that creates subscription when executed

        Example:
            >>> OnChange(User.profile.on_child_change("email"), HandleEmailChange())
        """
        from every_pv.morphisms import OnChildChangeOp

        return OnChildChangeOp(self, address)

    def on_children_change(self) -> OnChildrenChangeOp:
        """Subscribe to changes on all children.

        Returns:
            OnChildrenChangeOp that creates subscription when executed

        Example:
            >>> OnChange(Users.on_children_change(), SyncUsers())
        """
        from every_pv.morphisms import OnChildrenChangeOp

        return OnChildrenChangeOp(self)

    def on_descendants_change(self, *pattern: key.KeySegment) -> OnDescendantsChangeOp:
        """Subscribe to changes on descendants matching a pattern.

        Args:
            *pattern: Key segments pattern (use "*" for wildcards)

        Returns:
            OnDescendantsChangeOp that creates subscription when executed

        Example:
            >>> OnChange(Users.on_descendants_change("*", "status"), HandleStatusChanges())
        """
        from every_pv.morphisms import OnDescendantsChangeOp

        return OnDescendantsChangeOp(self, *pattern)
