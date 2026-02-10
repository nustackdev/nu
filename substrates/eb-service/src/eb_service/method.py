"""method -- declarative method descriptor for service interfaces.

Eliminates boilerplate in Interface definitions. Instead of hand-wiring
ServiceMethodCall for each method, declare them as one-liners::

    class SolanaRpc(Interface):
        get_latest_blockhash = method(StrValue)
        get_balance = method(IntValue, "getBalance")

The descriptor auto-infers the service method name from the Python
attribute name via __set_name__, with optional explicit override.

Generic in V (the ValueBase subclass), so type checkers propagate the
specific return type through to autocomplete::

    sol.get_slot()              # pyright sees: IntValue
    sol.get_transaction().slot  # pyright sees: IntValue (chained)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.abc.values import ValueBase


if TYPE_CHECKING:
    from .interface import Interface


__all__ = [
    "method",
]


class _BoundMethod[V: ValueBase]:
    """A method descriptor bound to a specific Interface instance.

    Calling this produces a lazy Value term wrapping ServiceMethodCall.
    Generic in V so the type checker knows the return type.
    """

    __slots__ = ("_method_name", "_owner", "_value_type")

    def __init__(self, owner: Interface, value_type: type[V], method_name: str) -> None:
        self._owner = owner
        self._value_type = value_type
        self._method_name = method_name

    def __call__(self, *args: object, **kwargs: object) -> V:
        return self._owner.call(self._value_type, self._method_name, *args, **kwargs)

    def __repr__(self) -> str:
        owner = self._owner.__class__.__name__
        return f"{owner}.{self._method_name}"


class method[V: ValueBase]:  # noqa: N801
    """Descriptor that declares a service method on an Interface.

    Generic in V (a ValueBase subclass). When you write::

        get_slot = method(IntValue, "getSlot")

    pyright infers V = IntValue, so ``sol.get_slot()`` returns IntValue
    with full autocomplete for IntType methods, conversions, etc.

    Uses __set_name__ to auto-infer the service method name from the
    Python attribute name. An explicit name can be provided for APIs
    with different naming conventions (e.g. camelCase).
    """

    def __init__(self, value_type: type[V], name: str | None = None) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._attr_name: str = ""
        self._method_name: str = name or ""

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._method_name = self._explicit_name or attr_name

    @overload
    def __get__(self, obj: None, objtype: type) -> method[V]: ...
    @overload
    def __get__(self, obj: Interface, objtype: type | None = None) -> _BoundMethod[V]: ...

    def __get__(
        self, obj: Interface | None, objtype: type | None = None
    ) -> method[V] | _BoundMethod[V]:
        if obj is None:
            return self
        return _BoundMethod(obj, self._value_type, self._method_name)

    def __repr__(self) -> str:
        name = self._method_name or self._explicit_name or "?"
        return f"method({self._value_type.__name__}, {name!r})"
