# ruff: noqa: D102
"""Location capability protocols — CRUD + observe for location refs.

All protocol-only (no base implementations — substrates implement).

LocationGettableProtocol: get() -> T
LocationSettableProtocol: set(value: T) -> T
LocationExistableProtocol: exists() -> BoolValue, missing() -> BoolValue
LocationDeletableProtocol: delete() -> None
LocationObservableProtocol: on_change(callback) -> None
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from everybase import BoolValue


__all__ = [
    "LocationDeletableProtocol",
    "LocationExistableProtocol",
    "LocationGettableProtocol",
    "LocationObservableProtocol",
    "LocationSettableProtocol",
]


class LocationGettableProtocol[T](Protocol):
    """Protocol for location refs that can read their value.

    Implementations (PVPrimitiveRef, future PyRefBase) provide
    the actual storage access logic.
    """

    def get(self) -> T: ...


class LocationSettableProtocol[T](Protocol):
    """Protocol for location refs that can write a value.

    Implementations (PVPrimitiveRef, future PyRefBase) provide
    the actual storage write logic.
    """

    def set(self, value: T) -> T: ...


class LocationExistableProtocol(Protocol):
    """Protocol for location refs that can check existence.

    Implementations (PVPrimitiveRef, future PyRefBase) provide
    the actual existence check logic.
    """

    def exists(self) -> BoolValue: ...
    def missing(self) -> BoolValue: ...


class LocationDeletableProtocol(Protocol):
    """Protocol for location refs that can delete their value.

    Implementations (PVPrimitiveRef, future PyRefBase) provide
    the actual deletion logic.
    """

    def delete(self) -> None: ...


class LocationObservableProtocol[T](Protocol):
    """Protocol for location refs that can be observed for changes.

    Implementations (PVPrimitiveRef, future PyRefBase) provide
    the actual change observation logic.
    """

    def on_change(self, callback: Callable[[T], None]) -> None: ...
