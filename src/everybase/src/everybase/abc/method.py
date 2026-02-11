"""method descriptor and AutoInterface for declarative method proxying.

method: Descriptor that proxies method calls to underlying Python objects.
AutoInterface: Base class that auto-creates method descriptors from annotations.

Usage — explicit descriptors on instance types::

    class StrHelpers(TypeBase[str]):
        upper = method(StrValue, pure=True)
        strip = method(StrValue, pure=True)

Usage — explicit descriptors with ref factory (class-level access)::

    class Solana(Service):
        get_slot = method(IntValue, "getSlot")

    Solana.get_slot()  # → IntValue term with ServiceRef inside

Usage — auto from annotations::

    class StrHelpers(AutoInterface, TypeBase[str], pure=True):
        upper: StrValue
        lower: StrValue
        strip: StrValue
"""

from __future__ import annotations

import typing
from typing import TYPE_CHECKING, overload

from everybase.abc.values import ValueBase
from everybase.core import Ref

from .morphisms import MethodCallCmd, MethodCallOp


if TYPE_CHECKING:
    from collections.abc import Callable

    from everybase.core import Term


__all__ = [
    "AutoInterface",
    "method",
]


class _BoundMethod[V: ValueBase]:
    """Method descriptor bound to a specific instance.

    Calling this creates a MethodCallOp (pure) or MethodCallCmd (impure)
    morphism wrapping the call, then wraps it in value_type.
    """

    __slots__ = ("_method_name", "_owner", "_pure", "_value_type")

    def __init__(self, owner: object, value_type: type[V], method_name: str, *, pure: bool) -> None:
        self._owner = owner
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(self._owner, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"{self._owner!r}.{self._method_name}"


class _ClassBoundMethod[V: ValueBase]:
    """Method descriptor bound to a class via a ref factory.

    The factory creates a ref term (e.g., ServiceRef) that resolves
    the target object from context at execution time.

    Solana.get_slot() creates:
        IntValue(MethodCallCmd(SolanaRef(), "getSlot"))
    where SolanaRef() is a ref term that does ctx.get(SolanaClient).
    """

    __slots__ = ("_method_name", "_pure", "_ref_factory", "_value_type")

    def __init__(
        self,
        ref_factory: Callable[[], Term],
        value_type: type[V],
        method_name: str,
        *,
        pure: bool,
    ) -> None:
        self._ref_factory = ref_factory
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        target = self._ref_factory()
        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(target, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"<class>.{self._method_name}"


class method[V: ValueBase]:  # noqa: N801
    """Descriptor that proxies method calls.

    Generic in V (a ValueBase subclass). Pyright infers the return type.

    Two access modes:
    - Instance access (e.g., my_str.upper()): creates MethodCall with
      the instance as target.
    - Class access with ref factory: creates MethodCall with a ref
      from the factory as target (context-resolved at execution time).

    The ref factory is set externally (e.g., by Interface.__init_subclass__)
    via the ``bind_ref_factory()`` method.

    Uses __set_name__ to auto-infer the method name from the Python
    attribute name. An explicit name can be provided for APIs with
    different naming conventions.
    """

    def __init__(self, value_type: type[V], name: str | None = None, *, pure: bool = False) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._pure = pure
        self._attr_name: str = ""
        self._method_name: str = name or ""
        self._ref_factory: Callable[[], Term] | None = None

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._method_name = self._explicit_name or attr_name

    def bind_ref_factory(self, factory: Callable[[], Term]) -> None:
        """Set the ref factory for class-level access.

        Called by base classes (e.g., Interface.__init_subclass__)
        to wire up context resolution.
        """
        self._ref_factory = factory

    @overload
    def __get__(self, obj: None, objtype: type) -> _ClassBoundMethod[V]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> _BoundMethod[V]: ...

    def __get__(
        self, obj: object | None, objtype: type | None = None
    ) -> method[V] | _BoundMethod[V] | _ClassBoundMethod[V]:
        if obj is None:
            # 1. Explicit ref factory (set by Interface.__init_subclass__)
            if self._ref_factory is not None:
                return _ClassBoundMethod(
                    self._ref_factory, self._value_type, self._method_name, pure=self._pure
                )
            # 2. Owner is a Ref subclass — use it directly as factory
            if objtype is not None and issubclass(objtype, Ref):
                return _ClassBoundMethod(
                    objtype, self._value_type, self._method_name, pure=self._pure
                )
            return self
        return _BoundMethod(obj, self._value_type, self._method_name, pure=self._pure)

    def __repr__(self) -> str:
        name = self._method_name or self._explicit_name or "?"
        purity = "pure" if self._pure else "impure"
        return f"method({self._value_type.__name__}, {name!r}, {purity})"


class AutoInterface:
    """Base class that auto-creates method descriptors from annotations.

    Inherit alongside TypeBase. Annotations of ValueBase subclasses
    become ``method()`` descriptors automatically.

    Usage::

        class StrHelpers(AutoInterface, TypeBase[str], pure=True):
            upper: StrValue
            lower: StrValue
            strip: StrValue

    Each annotation becomes ``method(AnnotationType, "attr_name", pure=<default>)``.
    Explicit ``method()`` assignments in the class body are preserved.
    """

    def __init_subclass__(cls, *, pure: bool = False, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        own_names = set(cls.__dict__.get("__annotations__", {}))
        if not own_names:
            return

        try:
            hints = typing.get_type_hints(cls)
        except Exception:
            return

        for name in own_names:
            if name.startswith("_"):
                continue
            # Skip if class body already has an explicit value (descriptor, method, etc.)
            if name in cls.__dict__ and name != "__annotations__":
                existing = cls.__dict__[name]
                if not isinstance(existing, type):
                    continue
            hint = hints.get(name)
            if hint is not None and isinstance(hint, type) and issubclass(hint, ValueBase):
                setattr(cls, name, method(hint, name, pure=pure))
