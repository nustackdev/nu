# ruff: noqa: D102
"""Reactive view protocols — structural contracts for observable views.

These protocols formalize what storage views must implement for
reactive ops (change observation) to operate on them.

Used by ops via isinstance() checks instead of hasattr().
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = [
    "ChildObservableProtocol",
    "ChildrenObservableProtocol",
    "DescendantsObservableProtocol",
    "ObservableProtocol",
]


@runtime_checkable
class ObservableProtocol(Protocol):
    """View that can be observed for changes."""

    def on_change(self) -> object: ...


@runtime_checkable
class ChildObservableProtocol(Protocol):
    """View that can observe changes on a specific child by address."""

    def on_child_change(self, address: object) -> object: ...


@runtime_checkable
class ChildrenObservableProtocol(Protocol):
    """View that can observe changes on all immediate children."""

    def on_children_change(self) -> object: ...


@runtime_checkable
class DescendantsObservableProtocol(Protocol):
    """View that can observe changes on descendants matching a pattern."""

    def on_descendents_change(self, first: object, *rest: object) -> object: ...
