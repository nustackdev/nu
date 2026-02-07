"""method -- declarative method descriptor for service interfaces.

Eliminates boilerplate in Interface definitions. Instead of hand-wiring
ServiceMethodCall for each method, declare them as one-liners::

    class SolanaRpc(Interface):
        get_latest_blockhash = method(StrValue)
        get_balance = method(IntValue, "getBalance")

The descriptor auto-infers the service method name from the Python
attribute name via __set_name__, with optional explicit override.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everybase.abc import ValueBase


__all__ = [
    "method",
]


class method:  # noqa: N801
    """Descriptor that declares a service method on an Interface.

    Uses __set_name__ to auto-infer the service method name from the
    Python attribute name. An explicit name can be provided for APIs
    with different naming conventions (e.g. camelCase).

    Args:
        value_type: The Value class for the return type (e.g. IntValue, DictValue).
        name: Optional explicit service method name. Defaults to the attribute name.
    """

    def __init__(self, value_type: type[ValueBase], name: str | None = None) -> None:
        self._value_type = value_type
        self._explicit_name = name

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._method_name = self._explicit_name or attr_name

    def __get__(self, obj: object, objtype: type | None = None) -> method | _BoundMethod:
        if obj is None:
            return self
        return _BoundMethod(obj, self._value_type, self._method_name)

    def __repr__(self) -> str:
        name = getattr(self, "_method_name", self._explicit_name or "?")
        return f"method({self._value_type.__name__}, {name!r})"


class _BoundMethod:
    """A method descriptor bound to a specific Interface instance.

    Calling this produces a lazy Value term wrapping ServiceMethodCall.
    """

    __slots__ = ("_method_name", "_owner", "_value_type")

    def __init__(self, owner: object, value_type: type[ValueBase], method_name: str) -> None:
        self._owner = owner
        self._value_type = value_type
        self._method_name = method_name

    def __call__(self, *args: object, **kwargs: object) -> ValueBase:
        return self._owner.call(self._value_type, self._method_name, *args, **kwargs)

    def __repr__(self) -> str:
        owner = self._owner.__class__.__name__
        return f"{owner}.{self._method_name}"
